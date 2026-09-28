import os
import tempfile
import sqlite3
import pytest
from unittest.mock import patch
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.pipeline import ingest_raw_event, ingest_and_process_atomic
from app.correction import process_and_apply_corrections
from app.models import RawEvent, DailyReport, ReportVersion, AuditLog

@pytest.fixture
def fail_db():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_failure.db")
    db_url = f"sqlite:///{db_path}"

    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False, "timeout": 15}
    )

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

def test_failure_injection_during_report_mutation_rolls_back_raw_event(fail_db):
    """
    Failure Injection Test 1:
    Forces an exception during correction recalculation after raw event is staged.
    Verifies that the entire transaction rolls back, leaving no orphaned RawEvent.
    """
    session, engine = fail_db
    target_event_id = "EVT-FAIL-INJECT-01"
    evt = {
        "event_id": target_event_id,
        "domain": "RTC-Attendance",
        "student_id": "RTC-STU-0001",
        "event_timestamp": "2026-08-20T09:00:00",
        "arrival_timestamp": "2026-08-20T09:15:00",
        "batch_id": "BATCH-FAIL",
        "payload": {"attendance_status": "Present", "class_id": "CS-301", "attendance_date": "2026-08-20"}
    }

    # Simulate unexpected runtime error inside process_and_apply_corrections
    with patch("app.correction.extract_event_metric_contribution", side_effect=RuntimeError("Simulated Database I/O Failure")):
        with pytest.raises(RuntimeError):
            ingest_and_process_atomic(session, evt)

    # Invariant: Neither RawEvent nor DailyReport should exist in database
    persisted_event = session.query(RawEvent).filter(RawEvent.event_id == target_event_id).first()
    assert persisted_event is None, "RawEvent was committed despite downstream transaction failure!"

    reports_count = session.query(DailyReport).count()
    assert reports_count == 0, "DailyReport was created despite transaction failure!"

def test_failure_injection_during_version_creation(fail_db):
    """
    Failure Injection Test 2:
    Simulates a failure during ReportVersion creation.
    Verifies that no partial report version, correction, or raw event remains committed.
    """
    session, engine = fail_db
    target_event_id = "EVT-FAIL-INJECT-02"
    evt = {
        "event_id": target_event_id,
        "domain": "RTC-Assessment",
        "student_id": "RTC-STU-0002",
        "event_timestamp": "2026-08-20T10:00:00",
        "arrival_timestamp": "2026-08-20T10:30:00",
        "batch_id": "BATCH-FAIL-2",
        "payload": {"assessment_type": "Mid-Term", "subject": "Networks", "score": 88.0}
    }

    original_add = session.add
    def faulty_add(instance):
        if isinstance(instance, ReportVersion):
            raise ValueError("Simulated failure during ReportVersion persistence")
        return original_add(instance)

    with patch.object(session, "add", side_effect=faulty_add):
        with pytest.raises(ValueError):
            ingest_and_process_atomic(session, evt)

    persisted_event = session.query(RawEvent).filter(RawEvent.event_id == target_event_id).first()
    assert persisted_event is None, "RawEvent was committed despite ReportVersion failure!"
