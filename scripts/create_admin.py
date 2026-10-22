import getpass
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    name=input('Administrator name: ').strip()
    email=input('Administrator email: ').strip().lower()
    password=getpass.getpass('Administrator password (10+ characters): ')
    if len(name)<2 or '@' not in email or len(password)<10:
        raise SystemExit('Enter a valid name/email and a password of at least 10 characters.')
    db.create_all()
    existing=User.query.filter_by(email=email).first()
    if existing:
        raise SystemExit('That email already exists. Choose another address; this script never silently promotes an existing account.')
    db.session.add(User(name=name,email=email,password_hash=generate_password_hash(password),role='admin'))
    db.session.commit()
    print('Administrator account created.')
