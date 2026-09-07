import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.pipeline import ingest_raw_event
from app.correction import process_and_apply_corrections, compute_ground_truth, review_pending_correction
from app.models import DailyReport, ReportVersion, ReportCorrection

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_on_time_correction_and_ground_truth(db):
    target_date = "2026-08-20"
    for i in range(1, 4):
        e_data = {
            "event_id": f"TEST-EVT-CORR-{i}",
            "domain": "RTC-Attendance",
            "student_id": f"RTC-STU-{i:04d}",
            "event_timestamp": f"{target_date}T09:00:00",
            "arrival_timestamp": f"{target_date}T09:30:00",
            "batch_id": "BATCH-01",
            "payload": {"attendance_status": "Present", "class_id": "CS-301", "attendance_date": target_date}
        }
        ingest_raw_event(db, e_data)
        process_and_apply_corrections(db, f"TEST-EVT-CORR-{i}")

    gt = compute_ground_truth(db, target_date, "RTC-Attendance")
    assert gt == 3.0

    report = db.query(DailyReport).filter(DailyReport.reporting_date == target_date, DailyReport.domain == "RTC-Attendance").first()
    assert report is not None
    assert report.corrected_aggregate == 3.0
    assert report.ground_truth_aggregate == 3.0
    assert report.corrected_error == 0.0

def test_late_event_recalculation(db):
    target_date = "2026-08-20"
    # On-time event
    e1 = {
        "event_id": "TEST-EVT-LATE-01",
        "domain": "RTC-Attendance",
        "student_id": "RTC-STU-0001",
        "event_timestamp": f"{target_date}T09:00:00",
        "arrival_timestamp": f"{target_date}T09:30:00",
        "batch_id": "BATCH-01",
        "payload": {"attendance_status": "Present", "class_id": "CS-301", "attendance_date": target_date}
    }
    ingest_raw_event(db, e1)
    process_and_apply_corrections(db, "TEST-EVT-LATE-01")

    report1 = db.query(DailyReport).filter(DailyReport.reporting_date == target_date, DailyReport.domain == "RTC-Attendance").first()
    assert report1.corrected_aggregate == 1.0
    assert report1.current_version == 2 # Initial + 1

    # Late event arrives 3 days later
    e2_late = {
        "event_id": "TEST-EVT-LATE-02",
        "domain": "RTC-Attendance",
        "student_id": "RTC-STU-0002",
        "event_timestamp": f"{target_date}T09:00:00", # August 20
        "arrival_timestamp": "2026-08-23T15:00:00", # August 23
        "batch_id": "BATCH-02",
        "payload": {"attendance_status": "Present", "class_id": "CS-301", "attendance_date": target_date}
    }
    ingest_raw_event(db, e2_late)
    proc_res = process_and_apply_corrections(db, "TEST-EVT-LATE-02")

    db.refresh(report1)
    assert report1.corrected_aggregate == 2.0
    assert report1.current_version == 3
    assert report1.status == "CORRECTED"

def test_high_impact_forced_review(db):
    target_date = "2026-08-20"
    hi_evt = {
        "event_id": "TEST-EVT-HI-REV",
        "domain": "RTC-Placement",
        "student_id": "RTC-STU-0001",
        "event_timestamp": f"{target_date}T10:00:00",
        "arrival_timestamp": "2026-08-24T12:00:00", # Late
        "batch_id": "BATCH-HI",
        "payload": {
            "drive_id": "DRIVE-GOOGLE",
            "registration_status": "Registered",
            "offer_status": "Offered",
            "is_placement_status_change": True # Forced Review
        }
    }
    ingest_raw_event(db, hi_evt)
    proc_res = process_and_apply_corrections(db, "TEST-EVT-HI-REV")

    assert proc_res["requires_review"] == True
    
    corr = db.query(ReportCorrection).filter(ReportCorrection.correction_id == proc_res["correction_id"]).first()
    assert corr.status == "PENDING_REVIEW"

    # Approve review
    app_res = review_pending_correction(db, corr.correction_id, "APPROVE")
    assert app_res["status"] == "APPROVED"
    assert app_res["aggregate"] == 1.0
