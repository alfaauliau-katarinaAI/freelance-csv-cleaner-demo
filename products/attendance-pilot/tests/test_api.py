import io
import uuid
from PIL import Image
from fastapi.testclient import TestClient
import pytest
from app import main


@pytest.fixture
def ctx(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'DB_PATH',tmp_path/'private'/'attendance.sqlite3')
    monkeypatch.setattr(main,'PHOTO_DIR',tmp_path/'private'/'photos')
    with TestClient(main.app) as admin:
        main.create_user('owner','Pemilik Toko','Correct-Horse-2026',role='admin')
        assert admin.post('/api/login',json={'username':'owner','password':'Correct-Horse-2026'}).status_code==200
        res=admin.post('/api/sites',json={'name':'Kantor','lat':-7.9826,'lon':112.6302,'radius_m':100})
        assert res.status_code==201
        assert admin.post('/api/employees',json={'username':'sari','display_name':'Sari','password':'Employee-Strong-2026','site_id':res.json()['id']}).status_code==201
        employee=TestClient(main.app)
        assert employee.post('/api/login',json={'username':'sari','password':'Employee-Strong-2026'}).status_code==200
        yield admin,employee
        employee.close()


def photo():
    image=Image.new('RGB',(220,220),'#eee')
    buf=io.BytesIO()
    image.save(buf,format='JPEG')
    return ('selfie.jpg',buf.getvalue(),'image/jpeg')


def attend(client,kind='IN',lat=-7.9826,lon=112.6302,accuracy=12,key=None,photo_file=None):
    return client.post('/api/attendance',data={'kind':kind,'lat':lat,'lon':lon,'accuracy_m':accuracy,'request_key':key or str(uuid.uuid4())},files={'photo':photo_file or photo()})


def test_authz(ctx):
    admin,employee=ctx
    assert employee.get('/api/me').json()['role']=='employee'
    assert employee.get('/api/employees').status_code==403
    assert employee.post('/api/sites',json={'name':'Fake','lat':0,'lon':0,'radius_m':20}).status_code==403
    assert TestClient(main.app).get('/api/history').status_code==401


def test_geo_and_accuracy(ctx):
    _,emp=ctx
    assert attend(emp,lon=113.1).status_code==422
    assert attend(emp,accuracy=80).status_code==422
    assert attend(emp,lat=91).status_code==400
    assert emp.get('/api/history').json()==[]


def test_photo_checks(ctx):
    _,emp=ctx
    bad=('fake.jpg',b'not a photo'*100,'image/jpeg')
    assert attend(emp,photo_file=bad).status_code==400
    assert emp.get('/api/history').json()==[]


def test_checkin_checkout_idempotency(ctx):
    _,emp=ctx
    token=str(uuid.uuid4())
    ok=attend(emp,key=token)
    assert ok.status_code==201,ok.text
    assert ok.json()['kind']=='IN'
    assert attend(emp,key=token).json()['repeat'] is True
    assert attend(emp).status_code==422
    assert attend(emp,kind='OUT').status_code==201
    assert attend(emp,kind='OUT').status_code==422
    assert len(emp.get('/api/history').json())==2


def test_private_photos_admin_and_employee(ctx):
    admin,emp=ctx
    entry=attend(emp).json()
    assert emp.get('/api/photos/'+entry['id']).status_code==200
    assert admin.get('/api/photos/'+entry['id']).status_code==200
    assert emp.get('/api/photos/'+str(uuid.uuid4())).status_code==404
    assert admin.get('/api/report.csv').status_code==200
    assert emp.get('/api/report.csv').status_code==403


def test_logout(ctx):
    _,emp=ctx
    assert emp.post('/api/logout').status_code==200
    assert emp.get('/api/me').status_code==401


def test_input_validation(ctx):
    admin,emp=ctx
    assert admin.post('/api/sites',json={'name':'X','lat':0,'lon':0,'radius_m':1}).status_code==422
    assert admin.post('/api/employees',json={'username':'weak','display_name':'Weak','password':'short','site_id':1}).status_code==422
    assert attend(emp,key='invalid').status_code==400


def test_csv_injection_escaping():
    assert main.safe_csv('=1+1')=="'=1+1"
    assert main.safe_csv('Normal')=='Normal'


def test_haversine_zero():
    assert main.haversine(-7.98,112.63,-7.98,112.63)==0
    assert 100<main.haversine(0,0,0,0.001)<120
