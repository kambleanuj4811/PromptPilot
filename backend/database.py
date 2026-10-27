"""SQLAlchemy engine, session factory, and table creation (SQLite)."""
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    pass


_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Create folders and tables. Safe to call on every startup."""
    from backend.models import database_models  # noqa: F401  (registers the tables)

    db_file = engine.url.database
    if db_file and db_file != ":memory:":
        Path(db_file).parent.mkdir(parents=True, exist_ok=True)
    settings.chroma_persist_directory.mkdir(parents=True, exist_ok=True)
    settings.upload_directory.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency: one session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()