import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from db.models import Base

# Database URL from environment (default to local sqlite)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Ensure the storage directory exists
    os.makedirs("storage", exist_ok=True)
    DATABASE_URL = "sqlite:///storage/parikshak.db"

# Configure the engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL configuration
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600
    )

# Session factories
session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
SessionLocal = scoped_session(session_factory)

def init_db():
    """Create all tables defined in Base if they do not exist."""
    Base.metadata.create_all(engine)

def get_db_session():
    """Dependency generator for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
