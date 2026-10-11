"""Pilot operator CLI: python -m app.manage add-admin --username admin --name Pemilik"""
import argparse
import getpass
import sqlite3
from .main import init_db, create_user


def main():
    parser=argparse.ArgumentParser(description='KATARINA Attendance admin bootstrap')
    subs=parser.add_subparsers(dest='action',required=True)
    add=subs.add_parser('add-admin')
    add.add_argument('--username',required=True)
    add.add_argument('--name',required=True)
    args=parser.parse_args()
    if args.action=='add-admin':
        password=getpass.getpass('Password admin (minimal 12 karakter): ')
        confirm=getpass.getpass('Ulangi password: ')
        if password!=confirm:
            parser.error('Password tidak cocok')
        init_db()
        try:
            pk=create_user(args.username,args.name,password,role='admin')
        except (ValueError,sqlite3.IntegrityError) as err:
            parser.error(str(err))
        print(f'Admin dibuat (id {pk}). Password tidak disimpan di log.')


if __name__=='__main__':main()
