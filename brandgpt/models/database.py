from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from brandgpt.config import settings

# SQLite specific configuration
connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}

# Configure connection pool to support concurrent background tasks
# SQLAlchemy default: pool_size=5 + max_overflow=10 = 15 total connections
# Configured for: pool_size=20 + max_overflow=30 = 50 total (configurable via env vars)
# This prevents connection exhaustion when multiple ingestion batches run concurrently
engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_size=settings.db_pool_size,           # Core connection pool (DB_POOL_SIZE)
    max_overflow=settings.db_max_overflow,     # Additional connections (DB_MAX_OVERFLOW)
    pool_pre_ping=True,                        # Verify connections before using
    pool_recycle=settings.db_pool_recycle      # Recycle after N seconds (DB_POOL_RECYCLE)
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()