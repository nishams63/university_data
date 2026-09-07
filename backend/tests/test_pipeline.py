import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.pipeline import ingest_raw_event
from app.models import RawEvent, AuditLog

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_on_time_event_ingestion(db):
    event_data = {
        "event_id": "TEST-EVT-001",
        "domain": "RTC-Attendance",
        "student_id": "RTC-STU-0001",
        "event_timestamp": "2026-08-20T09:00:00",
        "arrival_timestamp": "2026-08-20T10:00:00", # 1 hour delay <= 24h
        "batch_id": "BATCH-01",
        "payload": {"attendance_status": "Present", "class_id": "CS-301", "attendance_date": "2026-08-20"}
    }
    res = ingest_raw_event(db, event_data)
    assert res["status"] == "INGESTED"
    assert res["is_late"] == False
    assert res["is_valid"] == True

def test_late_event_ingestion(db):
    event_data = {
        "event_id": "TEST-EVT-002",
        "domain": "RTC-Attendance",
        "student_id": "RTC-STU-0001",
        "event_timestamp": "2026-08-20T09:00:00",
        "arrival_timestamp": "2026-08-22T14:00:00", # 53 hours delay > 24h
        "batch_id": "BATCH-02",
        "payload": {"attendance_status": "Present", "class_id": "CS-301", "attendance_date": "2026-08-20"}
    }
    res = ingest_raw_event(db, event_data)
    assert res["status"] == "INGESTED"
    assert res["is_late"] == True

def test_idempotency_duplicate_discard(db):
    event_data = {
        "event_id": "TEST-EVT-003",
        "domain": "RTC-Assessment",
        "student_id": "RTC-STU-0002",
        "event_timestamp": "2026-08-20T10:00:00",
        "arrival_timestamp": "2026-08-20T11:00:00",
        "batch_id": "BATCH-01",
        "payload": {"assessment_type": "Mid-Term", "subject": "Data Structures", "score": 85.5}
    }
    res1 = ingest_raw_event(db, event_data)
    assert res1["status"] == "INGESTED"

    # Re-ingest exact same event_id
    res2 = ingest_raw_event(db, event_data)
    assert res2["status"] == "DUPLICATE"
    assert res2["is_valid"] == False

    # Check DB only contains 1 record for event_id
    count = db.query(RawEvent).filter(RawEvent.event_id == "TEST-EVT-003").count()
    assert count == 1

def test_invalid_payload_handling(db):
    invalid_data = {
        "event_id": "TEST-EVT-INV",
        "domain": "RTC-Assessment",
        "student_id": "RTC-STU-0003",
        "event_timestamp": "2026-08-20T10:00:00",
        "arrival_timestamp": "2026-08-20T11:00:00",
        "batch_id": "BATCH-INV",
        "payload": {"corrupt_field": True} # Missing score
    }
    res = ingest_raw_event(db, invalid_data)
    assert res["status"] == "INVALID"
    assert res["is_valid"] == False
