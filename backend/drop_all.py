import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, Base
import app.models

print("Dropping all tables...")
Base.metadata.drop_all(bind=engine)
print("Done.")
