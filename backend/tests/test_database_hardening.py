import os
import tempfile
import sqlite3
import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from app.database import Base, get_engine_diagnostics
from app.pipeline import ingest_raw_event, ingest_and_process_atomic
from app.correction import process_and_apply_corrections
from app.models import Student, RawEvent, DailyReport, ReportVersion, ReportCorrection

@pytest.fixture
def hardened_db():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_hardened.db")
    db_url = f"sqlite:///{db_path}"

    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False, "timeout": 15}
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if isinstance(dbapi_connection, sqlite3.Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA busy_timeout=10000;")
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.close()

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()

    yield session, engine

    session.close()
    engine.dispose()
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

def test_wal_mode_and_foreign_keys_enabled(hardened_db):
    session, engine = hardened_db
    diag = get_engine_diagnostics(session)
    assert diag["journal_mode"] == "wal", f"Expected WAL mode, got {diag['journal_mode']}"
    assert diag["foreign_keys"] == 1, f"Expected foreign_keys=1, got {diag['foreign_keys']}"
    assert diag["busy_timeout"] == 10000, f"Expected busy_timeout=10000, got {diag['busy_timeout']}"

def test_daily_report_composite_uniqueness(hardened_db):
    """
    Enforces UNIQUE(reporting_date, domain) at database schema level.
    """
    session, engine = hardened_db
    r1 = DailyReport(
        report_id="RPT-TEST-001",
        reporting_date="2026-08-20",
        domain="RTC-Attendance",
        current_version=1
    )
    session.add(r1)
    session.commit()

    # Attempt to insert identical (reporting_date, domain) under different report_id
    r2 = DailyReport(
        report_id="RPT-TEST-002",
        reporting_date="2026-08-20",
        domain="RTC-Attendance",
        current_version=1
    )
    session.add(r2)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

def test_report_version_monotonic_uniqueness(hardened_db):
    """
    Enforces UNIQUE(report_id, version_number) at database schema level.
    """
    session, engine = hardened_db
    r = DailyReport(
        report_id="RPT-TEST-VER",
        reporting_date="2026-08-21",
        domain="RTC-Assessment",
        current_version=1
    )
    session.add(r)
    session.commit()

    v1 = ReportVersion(
        report_id="RPT-TEST-VER",
        reporting_date="2026-08-21",
        domain="RTC-Assessment",
        version_number=1,
        aggregate_value=50.0,
        metric_name="total_assessment_marks",
        change_type="INITIAL"
    )
    session.add(v1)
    session.commit()

    # Attempt to insert duplicate version_number 1 for same report_id
    v1_dup = ReportVersion(
        report_id="RPT-TEST-VER",
        reporting_date="2026-08-21",
        domain="RTC-Assessment",
        version_number=1,
        aggregate_value=55.0,
        metric_name="total_assessment_marks",
        change_type="DUPLICATE_VERSION_ATTEMPT"
    )
    session.add(v1_dup)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

def test_late_event_threshold_boundaries(hardened_db):
    """
    Evaluates 24-hour lateness boundary:
    - 24.00 hours delay -> on-time (is_late=False)
    - 24.05 hours delay -> late (is_late=True)
    """
    session, engine = hardened_db
    
    # 24.0 hours exact delay
    evt_on_time = {
        "event_id": "EVT-BOUND-24H",
        "domain": "RTC-Attendance",
        "student_id": "RTC-STU-0001",
        "event_timestamp": "2026-08-20T09:00:00",
        "arrival_timestamp": "2026-08-21T09:00:00", # Exactly 24.0h
        "batch_id": "BATCH-BOUND",
        "payload": {"attendance_status": "Present", "class_id": "CS-301", "attendance_date": "2026-08-20"}
    }
    res1 = ingest_raw_event(session, evt_on_time)
    assert res1["status"] == "INGESTED"
    assert res1["is_late"] == False

    # 24.1 hours delay
    evt_late = {
        "event_id": "EVT-BOUND-24H-LATE",
        "domain": "RTC-Attendance",
        "student_id": "RTC-STU-0002",
        "event_timestamp": "2026-08-20T09:00:00",
        "arrival_timestamp": "2026-08-21T09:06:00", # 24.1h > 24.0h
        "batch_id": "BATCH-BOUND",
        "payload": {"attendance_status": "Present", "class_id": "CS-301", "attendance_date": "2026-08-20"}
    }
    res2 = ingest_raw_event(session, evt_late)
    assert res2["status"] == "INGESTED"
    assert res2["is_late"] == True

def test_high_impact_threshold_boundaries(hardened_db):
    """
    Tests high-impact threshold boundary (15.0% drift and abs delta >= 5.0).
    Initial aggregate = 50.0.
    - Adding 7.0 marks: drift = 7/50 = 14.0% (< 15%) -> auto-applied
    - Adding 8.0 marks: drift = 8/50 = 16.0% (>= 15%) -> pending review
    """
    session, engine = hardened_db
    target_date = "2026-08-20"

    # Seed initial assessment score of 50.0
    init_evt = {
        "event_id": "EVT-IMPACT-INIT",
        "domain": "RTC-Assessment",
        "student_id": "RTC-STU-0001",
        "event_timestamp": f"{target_date}T10:00:00",
        "arrival_timestamp": f"{target_date}T10:30:00",
        "batch_id": "BATCH-INIT",
        "payload": {"assessment_type": "Mid-Term", "subject": "Maths", "score": 50.0}
    }
    ingest_and_process_atomic(session, init_evt)

    # Late event adding 7.0 marks (14% drift)
    evt_sub_threshold = {
        "event_id": "EVT-IMPACT-14PCT",
        "domain": "RTC-Assessment",
        "student_id": "RTC-STU-0002",
        "event_timestamp": f"{target_date}T10:00:00",
        "arrival_timestamp": "2026-08-22T12:00:00", # Late
        "batch_id": "BATCH-LATE",
        "payload": {"assessment_type": "Mid-Term", "subject": "Maths", "score": 7.0}
    }
    res1 = ingest_and_process_atomic(session, evt_sub_threshold)
    assert res1["correction_result"]["requires_review"] == False
    assert res1["correction_result"]["is_high_impact"] == False

    # Late event adding 10.0 marks (drift on 57.0 is 10/57 = 17.5% >= 15%)
    evt_super_threshold = {
        "event_id": "EVT-IMPACT-17PCT",
        "domain": "RTC-Assessment",
        "student_id": "RTC-STU-0003",
        "event_timestamp": f"{target_date}T10:00:00",
        "arrival_timestamp": "2026-08-22T13:00:00", # Late
        "batch_id": "BATCH-LATE",
        "payload": {"assessment_type": "Mid-Term", "subject": "Maths", "score": 10.0}
    }
    res2 = ingest_and_process_atomic(session, evt_super_threshold)
    assert res2["correction_result"]["requires_review"] == True
    assert res2["correction_result"]["is_high_impact"] == True
