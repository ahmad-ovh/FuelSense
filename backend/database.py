import os
import shutil
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Resolve database URL dynamically based on environment
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if os.environ.get("VERCEL") == "1":
    # Under Vercel, the directory is read-only. Copy seeded DB to /tmp.
    db_path = "/tmp/fuelsense.db"
    original_db = os.path.join(BASE_DIR, 'fuelsense.db')
    if not os.path.exists(db_path) and os.path.exists(original_db):
        try:
            shutil.copy2(original_db, db_path)
        except Exception as e:
            # Fallback message
            print(f"Error copying DB to /tmp: {e}")
    DATABASE_URL = f"sqlite:///{db_path}"
else:
    # Local development
    DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'fuelsense.db')}"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

