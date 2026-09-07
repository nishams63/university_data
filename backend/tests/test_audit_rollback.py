import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.pipeline import ingest_raw_event
from app.correction import process_and_apply_corrections
from app.audit import execute_rollback
from app.models import DailyReport, ReportCorrection, ReportVersion, AuditLog

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_rollback_compensating_action(db):
    target_date = "2026-08-20"
    e1 = {
        "event_id": "EVT-RB-01",
        "domain": "RTC-Attendance",
        "student_id": "RTC-STU-0001",
        "event_timestamp": f"{target_date}T09:00:00",
        "arrival_timestamp": f"{target_date}T09:15:00",
        "batch_id": "BATCH-01",
        "payload": {"attendance_status": "Present", "class_id": "CS-301", "attendance_date": target_date}
    }
    ingest_raw_event(db, e1)
    process_and_apply_corrections(db, "EVT-RB-01")

    # Late event causing correction
    e2_late = {
        "event_id": "EVT-RB-02",
        "domain": "RTC-Attendance",
        "student_id": "RTC-STU-0002",
        "event_timestamp": f"{target_date}T09:00:00",
        "arrival_timestamp": "2026-08-23T10:00:00",
        "batch_id": "BATCH-02",
        "payload": {"attendance_status": "Present", "class_id": "CS-301", "attendance_date": target_date}
    }
    ingest_raw_event(db, e2_late)
    proc_res = process_and_apply_corrections(db, "EVT-RB-02")
    corr_id = proc_res["correction_id"]

    report = db.query(DailyReport).filter(DailyReport.reporting_date == target_date, DailyReport.domain == "RTC-Attendance").first()
    assert report.corrected_aggregate == 2.0
    v_before = report.current_version

    # Execute rollback
    rb_res = execute_rollback(db, corr_id, reason="Testing rollback")
    assert rb_res["status"] == "ROLLED_BACK"

    db.refresh(report)
    assert report.corrected_aggregate == 1.0
    assert report.current_version == v_before + 1

    # Check version entry change_type == "ROLLBACK"
    v_last = db.query(ReportVersion).filter(ReportVersion.report_id == report.report_id).order_by(ReportVersion.version_number.desc()).first()
    assert v_last.change_type == "ROLLBACK"

def test_rollback_idempotency_guard(db):
    target_date = "2026-08-20"
    e1 = {
        "event_id": "EVT-RB-IDEM-01",
        "domain": "RTC-Attendance",
        "student_id": "RTC-STU-0001",
        "event_timestamp": f"{target_date}T09:00:00",
        "arrival_timestamp": f"{target_date}T09:15:00",
        "batch_id": "BATCH-01",
        "payload": {"attendance_status": "Present", "class_id": "CS-301", "attendance_date": target_date}
    }
    ingest_raw_event(db, e1)
    process_and_apply_corrections(db, "EVT-RB-IDEM-01")

    e2 = {
        "event_id": "EVT-RB-IDEM-02",
        "domain": "RTC-Attendance",
        "student_id": "RTC-STU-0002",
        "event_timestamp": f"{target_date}T09:00:00",
        "arrival_timestamp": "2026-08-23T10:00:00",
        "batch_id": "BATCH-02",
        "payload": {"attendance_status": "Present", "class_id": "CS-301", "attendance_date": target_date}
    }
    ingest_raw_event(db, e2)
    proc_res = process_and_apply_corrections(db, "EVT-RB-IDEM-02")
    corr_id = proc_res["correction_id"]

    # First rollback
    rb1 = execute_rollback(db, corr_id)
    assert rb1["status"] == "ROLLED_BACK"

    # Second rollback on same correction_id (idempotent skip)
    rb2 = execute_rollback(db, corr_id)
    assert rb2["status"] == "ALREADY_ROLLED_BACK"
