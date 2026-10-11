import csv
from contextlib import contextmanager,asynccontextmanager
import hashlib
import hmac
import io
import math
import os
import secrets
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
DB_PATH = Path(os.environ.get("KATARINA_ATTENDANCE_DB", str(ROOT.parent / "private" / "attendance.sqlite3")))
PHOTO_DIR = Path(os.environ.get("KATARINA_ATTENDANCE_PHOTOS", str(ROOT.parent / "private" / "photos")))
TZ = ZoneInfo(os.getenv("KATARINA_ATTENDANCE_TZ", "Asia/Jakarta"))
ALLOWED_TYPES = {"image/jpeg": "JPEG", "image/png": "PNG"}
MAX_PHOTO_BYTES = 2 * 1024 * 1024
SESSION_SECONDS = 12 * 3600
PBKDF_ITER = 310000


@contextmanager
def db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=15, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS sites (
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
          lat REAL NOT NULL, lon REAL NOT NULL, radius_m INTEGER NOT NULL CHECK(radius_m BETWEEN 20 AND 1000));
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE,
          display_name TEXT NOT NULL, salt TEXT NOT NULL, pwd_hash TEXT NOT NULL,
          role TEXT NOT NULL CHECK(role IN ('admin','employee')),
          site_id INTEGER REFERENCES sites(id), enabled INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS sessions (
          token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
          expires INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS events (
          id TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
          site_id INTEGER NOT NULL REFERENCES sites(id), kind TEXT NOT NULL CHECK(kind IN ('IN','OUT')),
          server_time TEXT NOT NULL, lat REAL NOT NULL, lon REAL NOT NULL,
          accuracy_m REAL NOT NULL, distance_m REAL NOT NULL,
          photo_name TEXT NOT NULL, request_key TEXT NOT NULL,
          UNIQUE(user_id,request_key));
        CREATE INDEX IF NOT EXISTS events_user_time ON events(user_id,server_time);
        """)


def encode_password(password, salt=None):
    if len(password) < 12:
        raise ValueError("Password minimal 12 karakter")
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), PBKDF_ITER)
    return salt, digest.hex()


def create_user(username, display_name, password, role="employee", site_id=None):
    if role not in {"admin", "employee"}:
        raise ValueError("Role tidak valid")
    if not username or len(username) > 80 or len(display_name) > 120:
        raise ValueError("Identitas tidak valid")
    salt, pw_hash = encode_password(password)
    with db() as con:
        cur = con.execute("INSERT INTO users(username,display_name,salt,pwd_hash,role,site_id) VALUES(?,?,?,?,?,?)",
                          (username.strip().lower(), display_name.strip(), salt, pw_hash, role, site_id))
        return cur.lastrowid


def haversine(lat1, lon1, lat2, lon2):
    r = 6371000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return 2*r*math.asin(min(1, math.sqrt(a)))


class Login(BaseModel):
    username: str
    password: str


class SiteForm(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    radius_m: int = Field(ge=20, le=1000)


class EmployeeForm(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    display_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=12, max_length=256)
    site_id: int = Field(gt=0)


def principal(request: Request):
    token = request.cookies.get("katarina_session")
    if not token:
        raise HTTPException(401, "Silakan login")
    key = hashlib.sha256(token.encode()).hexdigest()
    with db() as con:
        row = con.execute("SELECT u.id,u.username,u.display_name,u.role,u.site_id,u.enabled,s.expires FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=?", (key,)).fetchone()
    if not row or row["expires"] < int(time.time()) or not row["enabled"]:
        raise HTTPException(401, "Sesi tidak aktif")
    return dict(row)


def admin_user(user=Depends(principal)):
    if user["role"] != "admin":
        raise HTTPException(403, "Hanya admin")
    return user


def validate_image(raw, mimetype):
    if mimetype not in ALLOWED_TYPES:
        raise HTTPException(400, "Foto harus JPEG atau PNG")
    if len(raw) > MAX_PHOTO_BYTES or len(raw) < 50:
        raise HTTPException(400, "Ukuran foto 50 byte sampai 2 MB")
    try:
        with Image.open(io.BytesIO(raw)) as img:
            img.verify()
        with Image.open(io.BytesIO(raw)) as img:
            if img.format != ALLOWED_TYPES[mimetype] or img.width < 100 or img.height < 100 or img.width * img.height > 12_000_000:
                raise ValueError("Dimensi atau format foto tidak valid")
            clean = img.convert("RGB")
            buff = io.BytesIO()
            clean.save(buff, format="JPEG", quality=82, optimize=True)
            return buff.getvalue()
    except (UnidentifiedImageError, ValueError, OSError):
        raise HTTPException(400, "Isi file bukan foto yang valid")


@asynccontextmanager
async def lifespan(_app):
    init_db()
    yield


app = FastAPI(title="KATARINA Attendance — Pilot", docs_url=None, redoc_url=None, lifespan=lifespan)


@app.middleware("http")
async def headers(request, call_next):
    if request.url.path.startswith("/api/") and request.method in ("POST","PUT","PATCH","DELETE"):
        origin = request.headers.get("origin")
        if origin and origin.rstrip("/") != os.getenv("KATARINA_PUBLIC_ORIGIN",str(request.base_url)).rstrip("/"):
            return Response(status_code=403,content="Origin tidak diizinkan")
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store" if request.url.path.startswith("/api/") else "public, max-age=120"
    response.headers["Content-Security-Policy"] = "default-src 'self'; connect-src 'self'; img-src 'self' blob: data:; script-src 'self'; style-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
    return response


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html", headers={"Cache-Control":"no-cache"})


@app.get("/service-worker.js")
def service_worker():
    return FileResponse(STATIC / "service-worker.js",media_type="application/javascript",headers={"Service-Worker-Allowed":"/","Cache-Control":"no-cache"})


@app.post("/api/login")
def login(data: Login, response: Response, request: Request):
    with db() as con:
        row = con.execute("SELECT * FROM users WHERE username=? AND enabled=1", (data.username.strip().lower(),)).fetchone()
    # Constant-time verification even when account is absent. Rate limiting should be added at reverse proxy before internet exposure.
    if row:
        salt, hashed = row["salt"], row["pwd_hash"]
    else:
        salt, hashed = "00"*16, "00"*32
    computed = hashlib.pbkdf2_hmac("sha256",data.password.encode(),bytes.fromhex(salt),PBKDF_ITER)
    if not row or not hmac.compare_digest(computed.hex(),hashed):
        raise HTTPException(401, "Pengguna atau password salah")
    session = secrets.token_urlsafe(40)
    with db() as con:
        con.execute("DELETE FROM sessions WHERE expires < ?",(int(time.time()),))
        con.execute("INSERT INTO sessions(token_hash,user_id,expires) VALUES(?,?,?)",(hashlib.sha256(session.encode()).hexdigest(), row["id"],int(time.time())+SESSION_SECONDS))
    secure = request.url.scheme == "https" or os.environ.get("KATARINA_FORCE_HTTPS") == "1"
    response.set_cookie("katarina_session",session,httponly=True,secure=secure,samesite="strict",max_age=SESSION_SECONDS,path="/")
    return {"message":"Login berhasil"}


@app.post("/api/logout")
def logout(response: Response, request: Request):
    token = request.cookies.get("katarina_session")
    if token:
        with db() as con:
            con.execute("DELETE FROM sessions WHERE token_hash=?",(hashlib.sha256(token.encode()).hexdigest(),))
    response.delete_cookie("katarina_session",path="/")
    return {"message":"Logout berhasil"}


@app.get("/api/me")
def me(user=Depends(principal)):
    return {k:user[k] for k in ("id","username","display_name","role","site_id")}


@app.get("/api/sites")
def sites(user=Depends(principal)):
    with db() as con:
        if user["role"]=="admin":
            records=con.execute("SELECT * FROM sites ORDER BY id").fetchall()
        else:
            records=con.execute("SELECT * FROM sites WHERE id=?",(user["site_id"],)).fetchall()
    return [dict(x) for x in records]


@app.post("/api/sites",status_code=201)
def create_site(info: SiteForm, user=Depends(admin_user)):
    with db() as con:
        cur=con.execute("INSERT INTO sites(name,lat,lon,radius_m) VALUES(?,?,?,?)",(info.name,info.lat,info.lon,info.radius_m))
        return {"id":cur.lastrowid,"name":info.name}


@app.post("/api/employees",status_code=201)
def create_employee(info: EmployeeForm, user=Depends(admin_user)):
    try:
        user_id=create_user(info.username,info.display_name,info.password,site_id=info.site_id)
    except sqlite3.IntegrityError:
        raise HTTPException(400,"Username sudah digunakan atau lokasi tidak ada")
    return {"id":user_id,"username":info.username}


@app.get("/api/employees")
def employees(user=Depends(admin_user)):
    with db() as con:
        rows=con.execute("SELECT id,username,display_name,role,site_id,enabled FROM users ORDER BY id").fetchall()
    return [dict(row) for row in rows]


@app.post("/api/attendance",status_code=201)
async def attendance(kind: Literal["IN","OUT"] = Form(...), lat:float=Form(...),lon:float=Form(...),
                     accuracy_m:float=Form(...),request_key:str=Form(...),photo:UploadFile=File(...),user=Depends(principal)):
    if user["role"]!="employee" or not user["site_id"]:
        raise HTTPException(403,"Akun ini bukan karyawan yang memiliki lokasi kerja")
    if not all(math.isfinite(x) for x in (lat,lon,accuracy_m)) or abs(lat)>90 or abs(lon)>180:
        raise HTTPException(400,"Koordinat tidak valid")
    if accuracy_m<=0 or accuracy_m>75:
        raise HTTPException(422,"GPS belum cukup akurat (maksimal 75 m); coba kembali di area terbuka")
    try:
        uuid.UUID(request_key)
    except ValueError:
        raise HTTPException(400,"Request ID tidak valid")
    with db() as con:
        site=con.execute("SELECT * FROM sites WHERE id=?",(user["site_id"],)).fetchone()
    if not site:
        raise HTTPException(400,"Lokasi kerja tidak ditemukan")
    dist=haversine(lat,lon,site["lat"],site["lon"])
    if dist>site["radius_m"]:
        raise HTTPException(422,f"Anda di luar radius lokasi kerja: {round(dist)} meter")
    raw=await photo.read(MAX_PHOTO_BYTES+1)
    cleaned=validate_image(raw,photo.content_type)
    event_id=str(uuid.uuid4());filename=event_id+".jpg"
    try:
        with db() as con:
            con.execute("BEGIN IMMEDIATE")
            existing=con.execute("SELECT * FROM events WHERE user_id=? AND request_key=?",(user["id"],request_key)).fetchone()
            if existing:
                return {"id":existing["id"],"kind":existing["kind"],"server_time":existing["server_time"],"distance_m":round(existing["distance_m"],1),"repeat":True}
            last=con.execute("SELECT kind FROM events WHERE user_id=? ORDER BY server_time DESC,id DESC LIMIT 1",(user["id"],)).fetchone()
            if kind=="OUT" and (not last or last["kind"]!="IN"):
                raise HTTPException(422,"Belum ada absen masuk yang aktif")
            if kind=="IN" and last and last["kind"]=="IN":
                raise HTTPException(422,"Masih ada absen masuk aktif; silakan absen pulang dahulu")
            filepath=PHOTO_DIR/filename
            # New unguessable filename; never expose as a static public path.
            with open(filepath,"xb") as out:
                out.write(cleaned)
            now=datetime.now(timezone.utc).isoformat()
            con.execute("INSERT INTO events(id,user_id,site_id,kind,server_time,lat,lon,accuracy_m,distance_m,photo_name,request_key) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                        (event_id,user["id"],site["id"],kind,now,lat,lon,accuracy_m,dist,filename,request_key))
            return {"id":event_id,"kind":kind,"server_time":now,"distance_m":round(dist,1),"repeat":False}
    except Exception:
        filepath=PHOTO_DIR/filename
        if filepath.exists():
            filepath.unlink()
        raise


@app.get("/api/history")
def history(user=Depends(principal)):
    with db() as con:
        if user["role"]=="admin":
            rows=con.execute("SELECT e.id,e.kind,e.server_time,e.distance_m,e.accuracy_m,u.display_name,s.name AS site FROM events e JOIN users u ON u.id=e.user_id JOIN sites s ON s.id=e.site_id ORDER BY e.server_time DESC LIMIT 500").fetchall()
        else:
            rows=con.execute("SELECT e.id,e.kind,e.server_time,e.distance_m,e.accuracy_m,u.display_name,s.name AS site FROM events e JOIN users u ON u.id=e.user_id JOIN sites s ON s.id=e.site_id WHERE e.user_id=? ORDER BY e.server_time DESC LIMIT 100",(user["id"],)).fetchall()
    return [dict(row) for row in rows]


@app.get("/api/photos/{event_id}")
def event_photo(event_id:str,user=Depends(principal)):
    try: uuid.UUID(event_id)
    except ValueError: raise HTTPException(404,"Tidak ditemukan")
    with db() as con:
        e=con.execute("SELECT user_id,photo_name FROM events WHERE id=?",(event_id,)).fetchone()
    if not e or (user["role"]!="admin" and e["user_id"]!=user["id"]):
        raise HTTPException(404,"Tidak ditemukan")
    return FileResponse(PHOTO_DIR/e["photo_name"],media_type="image/jpeg",headers={"Cache-Control":"private, no-store"})


def safe_csv(value):
    txt=str(value if value is not None else "")
    if txt.lstrip().startswith(("=","+","-","@")):
        return "'"+txt
    return txt


@app.get("/api/report.csv")
def report(user=Depends(admin_user)):
    with db() as con:
        rows=con.execute("SELECT u.display_name,s.name AS site,e.kind,e.server_time,e.distance_m,e.accuracy_m FROM events e JOIN users u ON u.id=e.user_id JOIN sites s ON s.id=e.site_id ORDER BY e.server_time DESC LIMIT 20000").fetchall()
    buf=io.StringIO();writer=csv.writer(buf)
    writer.writerow(["Nama","Lokasi kerja","Jenis","Waktu server (UTC)","Jarak (m)","Akurasi GPS (m)"])
    for row in rows:writer.writerow([safe_csv(v) for v in tuple(row)])
    return Response(content="\ufeff"+buf.getvalue(),media_type="text/csv; charset=utf-8",headers={"Content-Disposition":'attachment; filename="KATARINA_Absensi.csv"'})


app.mount("/static",StaticFiles(directory=STATIC),name="static")
