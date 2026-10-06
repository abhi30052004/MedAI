"""
Database session and engine configuration for Neon Postgres (serverless).
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Engine tuned for serverless Postgres (Neon):
#  - pool_pre_ping: detect stale connections after cold starts
#  - small pool_size: Neon has limited connections on free tier
#  - pool_recycle: rotate connections periodically
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=300,
    pool_timeout=30,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
