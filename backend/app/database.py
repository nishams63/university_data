import os
import sqlite3
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

connect_args = {"check_same_thread": False, "timeout": 15} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

# Apply SQLite WAL mode, busy timeout, and foreign key enforcement on every connection
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA busy_timeout=10000;")  # 10,000ms (10s) busy timeout for concurrent transactions
        cursor.execute("PRAGMA foreign_keys=ON;")      # Enforce relational integrity
        cursor.execute("PRAGMA synchronous=NORMAL;")   # Optimized for WAL reliability & high write throughput
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_engine_diagnostics(db_session=None):
    """
    Returns verified runtime SQLite PRAGMA and connection metrics.
    """
    should_close = False
    if db_session is None:
        db_session = SessionLocal()
        should_close = True

    diagnostics = {
        "engine_url": str(engine.url),
        "is_sqlite": settings.DATABASE_URL.startswith("sqlite"),
        "journal_mode": "unknown",
        "busy_timeout": 0,
        "foreign_keys": 0,
        "synchronous": "unknown"
    }

    try:
        if settings.DATABASE_URL.startswith("sqlite"):
            jm = db_session.execute(text("PRAGMA journal_mode;")).scalar()
            bt = db_session.execute(text("PRAGMA busy_timeout;")).scalar()
            fk = db_session.execute(text("PRAGMA foreign_keys;")).scalar()
            sync = db_session.execute(text("PRAGMA synchronous;")).scalar()

            diagnostics["journal_mode"] = str(jm).lower() if jm else "unknown"
            diagnostics["busy_timeout"] = int(bt) if bt is not None else 0
            diagnostics["foreign_keys"] = int(fk) if fk is not None else 0
            diagnostics["synchronous"] = str(sync) if sync is not None else "unknown"
    except Exception as e:
        diagnostics["error"] = str(e)
    finally:
        if should_close:
            db_session.close()

    return diagnostics
