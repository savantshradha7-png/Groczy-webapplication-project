import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import app, db

with app.app_context():
    db.create_all()
    print("Groczy tables are ready. Import groczy.sql first for the full indexed schema and sample categories, or run seed_data.py.")
