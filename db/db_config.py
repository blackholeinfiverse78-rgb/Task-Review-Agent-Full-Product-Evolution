import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from db.models import Base

logger = logging.getLogger("db_config")

# Database URL from environment (default to local sqlite)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    os.makedirs("storage", exist_ok=True)
    DATABASE_URL = "sqlite:///storage/parikshak.db"

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20, pool_recycle=3600)

session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
SessionLocal = scoped_session(session_factory)

# Columns added after initial schema — migrate existing DBs automatically
_REVIEW_MIGRATIONS = [
    ("failure_type",     "VARCHAR(50)"),
    ("failure_reasons",  "TEXT"),
    ("improvement_hints","TEXT"),
    ("missing_features", "TEXT"),
    ("whats_done_well",  "TEXT"),
    ("selected_task_id", "VARCHAR(100)"),
    ("selection_reason", "TEXT"),
    ("analysis_json",    "TEXT"),
]

def _migrate_reviews_table(conn) -> None:
    """Add any missing columns to the reviews table without dropping data."""
    try:
        existing = {row[1] for row in conn.execute(text("PRAGMA table_info(reviews)"))}
        for col_name, col_type in _REVIEW_MIGRATIONS:
            if col_name not in existing:
                conn.execute(text(f"ALTER TABLE reviews ADD COLUMN {col_name} {col_type}"))
                logger.info(f"[DB MIGRATION] Added column reviews.{col_name}")
    except Exception as e:
        logger.warning(f"[DB MIGRATION] reviews migration failed (non-fatal): {e}")

def init_db():
    """Create all tables and run column migrations."""
    Base.metadata.create_all(engine)
    if DATABASE_URL.startswith("sqlite"):
        with engine.connect() as conn:
            _migrate_reviews_table(conn)
            conn.commit()

def get_db_session():
    """Dependency generator for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
