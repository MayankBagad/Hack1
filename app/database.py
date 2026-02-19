import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


def _resolve_database_url() -> str:
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        if db_url.startswith("postgres://"):
            return db_url.replace("postgres://", "postgresql+psycopg://", 1)
        if db_url.startswith("postgresql://") and "+psycopg" not in db_url:
            return db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return db_url

    if os.getenv("VERCEL"):
        return "sqlite:////tmp/hackathon.db"
    return "sqlite:///./hackathon.db"


def _build_engine(db_url: str):
    engine_kwargs: dict = {}
    if db_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}

    try:
        return create_engine(db_url, **engine_kwargs), db_url
    except Exception:
        fallback_url = "sqlite:////tmp/hackathon.db" if os.getenv("VERCEL") else "sqlite:///./hackathon.db"
        fallback_kwargs = {"connect_args": {"check_same_thread": False}}
        return create_engine(fallback_url, **fallback_kwargs), fallback_url


DATABASE_URL = _resolve_database_url()
engine, EFFECTIVE_DATABASE_URL = _build_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
