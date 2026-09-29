import os
import tempfile
import sqlite3
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_engine_diagnostics
from app.pipeline import ingest_raw_event, ingest_and_process_atomic
from app.correction import process_and_apply_corrections, review_pending_correction, compute_ground_truth
from app.audit import execute_rollback
from app.models import Student, RawEvent, DailyReport, ReportVersion, ReportCorrection, AuditLog
from app.schemas import (
    EventIngestResponse, ReviewActionResponse, RollbackResponse,
    ReconciliationResponse, HealthStatusSimple
)

@pytest.fixture
def review3_db():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_review3.db")
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False, "timeout": 15},
        pool_pre_ping=True
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

# ==============================================================================
# 1. BOUNDARY VALUE TESTS (STEP 42)
# ==============================================================================

def test_exact_24_hour_lateness_boundary(review3_db):
    """
    Evaluates exact 24.0h threshold boundary:
    - Delay <= 24.00h -> on-time (is_late=False)
    - Delay > 24.00h -> late (is_late=True)
    """
    session, engine = review3_db
    
    # Test 1A: Exactly 24.00 hours delay (86400 seconds)
    evt_exact = {
        "event_id": "EVT-BOUND-24-00",
        "domain": "RTC-Attendance",
        "student_id": "RTC-STU-0001",
        "event_timestamp": "2026-08-20T08:00:00",
        "arrival_timestamp": "2026-08-21T08:00:00", # Exactly 24h
        "batch_id": "BATCH-BOUND",
        "payload": {"attendance_status": "Present", "class_id": "CS-101", "attendance_date": "2026-08-20"}
    }
    res_exact = ingest_raw_event(session, evt_exact)
    assert res_exact["status"] == "INGESTED"
    assert res_exact["is_late"] is False, "Exact 24.00h delay should not be flagged late (delay <= threshold)"

    # Test 1B: 24 hours + 1 minute delay (24.0167 hours)
    evt_over = {
        "event_id": "EVT-BOUND-24-01",
        "domain": "RTC-Attendance",
        "student_id": "RTC-STU-0002",
        "event_timestamp": "2026-08-20T08:00:00",
        "arrival_timestamp": "2026-08-21T08:01:00", # 24h + 1min
        "batch_id": "BATCH-BOUND",
        "payload": {"attendance_status": "Present", "class_id": "CS-101", "attendance_date": "2026-08-20"}
    }
    res_over = ingest_raw_event(session, evt_over)
    assert res_over["status"] == "INGESTED"
    assert res_over["is_late"] is True, "24h + 1min delay MUST be classified as late"

def test_impact_percentage_threshold_boundary(review3_db):
    """
    Evaluates 15.0% impact threshold boundary:
    Initial aggregate = 100.0 marks.
    - Adding 14.0 marks: drift = 14.0% (< 15.0%) -> AUTO_CORRECTED (no review required)
    - Adding 16.0 marks: drift = 16.0% (>= 15.0%) -> PENDING_REVIEW
    """
    session, engine = review3_db
    target_date = "2026-08-20"

    # Seed baseline assessment aggregate of 100.0
    init_evt = {
        "event_id": "EVT-IMPACT-100",
        "domain": "RTC-Assessment",
        "student_id": "RTC-STU-0001",
        "event_timestamp": f"{target_date}T09:00:00",
        "arrival_timestamp": f"{target_date}T09:15:00",
        "batch_id": "BATCH-INIT",
        "payload": {"assessment_type": "Mid-Term", "subject": "Data Structures", "score": 100.0}
    }
    ingest_and_process_atomic(session, init_evt)

    # Sub-threshold: 14.0 marks late (drift: 14.0%)
    evt_14 = {
        "event_id": "EVT-IMPACT-14-PCT",
        "domain": "RTC-Assessment",
        "student_id": "RTC-STU-0002",
        "event_timestamp": f"{target_date}T09:00:00",
        "arrival_timestamp": "2026-08-23T10:00:00", # Late
        "batch_id": "BATCH-LATE",
        "payload": {"assessment_type": "Mid-Term", "subject": "Data Structures", "score": 14.0}
    }
    res_14 = ingest_and_process_atomic(session, evt_14)
    corr_14 = res_14["correction_result"]
    assert corr_14["is_high_impact"] is False
    assert corr_14["requires_review"] is False

    # Super-threshold: 20.0 marks late (drift on 114.0 is 20/114 = 17.54% >= 15%)
    evt_20 = {
        "event_id": "EVT-IMPACT-20-PCT",
        "domain": "RTC-Assessment",
        "student_id": "RTC-STU-0003",
        "event_timestamp": f"{target_date}T09:00:00",
        "arrival_timestamp": "2026-08-23T11:00:00", # Late
        "batch_id": "BATCH-LATE",
        "payload": {"assessment_type": "Mid-Term", "subject": "Data Structures", "score": 20.0}
    }
    res_20 = ingest_and_process_atomic(session, evt_20)
    corr_20 = res_20["correction_result"]
    assert corr_20["is_high_impact"] is True
    assert corr_20["requires_review"] is True

def test_high_risk_academic_override(review3_db):
    """
    Evaluates forced human review override:
    Even with small numerical delta (e.g. 1.0 mark),
    is_high_risk_outcome=True MUST force PENDING_REVIEW.
    """
    session, engine = review3_db
    target_date = "2026-08-20"

    # Seed baseline
    init_evt = {
        "event_id": "EVT-OVERRIDE-INIT",
        "domain": "RTC-Assessment",
        "student_id": "RTC-STU-0001",
        "event_timestamp": f"{target_date}T09:00:00",
        "arrival_timestamp": f"{target_date}T09:15:00",
        "batch_id": "BATCH-INIT",
        "payload": {"assessment_type": "Mid-Term", "subject": "Algorithms", "score": 80.0}
    }
    ingest_and_process_atomic(session, init_evt)

    # Late event with delta = 1.0 mark (drift is only 1.25%), but high-risk flag = True
    override_evt = {
        "event_id": "EVT-OVERRIDE-RISK",
        "domain": "RTC-Assessment",
        "student_id": "RTC-STU-0002",
        "event_timestamp": f"{target_date}T09:00:00",
        "arrival_timestamp": "2026-08-23T10:00:00", # Late
        "batch_id": "BATCH-LATE",
        "payload": {
            "assessment_type": "Mid-Term",
            "subject": "Algorithms",
            "score": 1.0,
            "is_high_risk_outcome": True # Pass/Fail border status alteration
        }
    }
    res = ingest_and_process_atomic(session, override_evt)
    corr = res["correction_result"]
    assert corr["is_high_impact"] is True
    assert corr["requires_review"] is True

# ==============================================================================
# 2. INVALID STATE TRANSITIONS & GOVERNANCE GUARDS (STEP 27)
# ==============================================================================

def test_invalid_state_transitions_rejected(review3_db):
    """
    Tests strict rejection of invalid state transitions:
    - Approving an already approved correction
    - Rejecting an already approved correction
    - Approving an already rejected correction
    - Duplicate rollback on rolled back correction
    """
    session, engine = review3_db
    target_date = "2026-08-20"

    # 1. Ingest baseline & late high-impact event
    ingest_and_process_atomic(session, {
        "event_id": "EVT-GOV-01",
        "domain": "RTC-Attendance",
        "student_id": "RTC-STU-0001",
        "event_timestamp": f"{target_date}T09:00:00",
        "arrival_timestamp": f"{target_date}T09:15:00",
        "batch_id": "BATCH-01",
        "payload": {"attendance_status": "Present", "class_id": "CS-101", "attendance_date": target_date}
    })

    late_res = ingest_and_process_atomic(session, {
        "event_id": "EVT-GOV-02",
        "domain": "RTC-Attendance",
        "student_id": "RTC-STU-0002",
        "event_timestamp": f"{target_date}T09:00:00",
        "arrival_timestamp": "2026-08-24T10:00:00", # 97 hours late
        "batch_id": "BATCH-02",
        "payload": {"attendance_status": "Present", "class_id": "CS-101", "attendance_date": target_date, "is_high_risk_outcome": True}
    })
    corr_id = late_res["correction_result"]["correction_id"]

    # First Approval -> should succeed
    app_res1 = review_pending_correction(session, corr_id, "APPROVE", reviewer_name="Dean of Academics")
    assert app_res1["status"] == "APPROVED"

    # Second Approval on same correction -> must be rejected as already approved
    app_res2 = review_pending_correction(session, corr_id, "APPROVE", reviewer_name="Dean of Academics")
    assert app_res2["status"] == "ERROR"
    assert "already approved" in app_res2["message"].lower()

    # Attempt Rejection on already approved correction -> must be rejected
    rej_res = review_pending_correction(session, corr_id, "REJECT", reviewer_name="HOD")
    assert rej_res["status"] == "ERROR"
    assert "already approved" in rej_res["message"].lower()

    # Compensating Rollback -> should succeed first time
    rb1 = execute_rollback(session, corr_id, reason="Testing rollback transition")
    assert rb1["status"] == "ROLLED_BACK"

    # Duplicate Rollback on already rolled-back correction -> must return ALREADY_ROLLED_BACK
    rb2 = execute_rollback(session, corr_id, reason="Duplicate attempt")
    assert rb2["status"] == "ALREADY_ROLLED_BACK"

# ==============================================================================
# 3. SCHEMA INTEGRITY & PYDANTIC RESPONSE CONTRACTS (STEP 30)
# ==============================================================================

def test_explicit_pydantic_schema_validation(review3_db):
    """
    Validates that API return payloads conform strictly to explicit Pydantic response models.
    """
    session, engine = review3_db
    diag = get_engine_diagnostics(session)

    # 1. Health Status Schema
    health_payload = {
        "status": "healthy",
        "database": "connected",
        "journal_mode": diag["journal_mode"],
        "foreign_keys": bool(diag["foreign_keys"]),
        "busy_timeout_ms": diag["busy_timeout"],
        "institution": "RATHINAM TECHNICAL CAMPUS (AUTONOMOUS)"
    }
    health_obj = HealthStatusSimple(**health_payload)
    assert health_obj.journal_mode == "wal"
    assert health_obj.foreign_keys is True

    # 2. Ingest Response Schema
    ingest_payload = {
        "status": "INGESTED",
        "event_id": "EVT-SCHEMA-01",
        "reporting_date": "2026-08-20",
        "is_late": False,
        "is_valid": True,
        "message": None,
        "correction_result": {"status": "PROCESSED"}
    }
    ingest_obj = EventIngestResponse(**ingest_payload)
    assert ingest_obj.status == "INGESTED"

    # 3. Review Action Schema
    review_payload = {
        "status": "APPROVED",
        "correction_id": "CORR-20260820-001",
        "action": "APPROVE",
        "new_version": 2,
        "aggregate": 42.0,
        "reviewer_name": "RTC Data Administrator"
    }
    review_obj = ReviewActionResponse(**review_payload)
    assert review_obj.status == "APPROVED"
    assert review_obj.aggregate == 42.0

    # 4. Rollback Response Schema
    rollback_payload = {
        "status": "ROLLED_BACK",
        "correction_id": "CORR-20260820-001",
        "report_id": "RTC-RPT-20260820-RTC-Attendance",
        "previous_val": 42.0,
        "restored_val": 35.0,
        "new_version": 3,
        "message": "Successfully executed compensating rollback."
    }
    rb_obj = RollbackResponse(**rollback_payload)
    assert rb_obj.new_version == 3

# ==============================================================================
# 4. FULL END-TO-END LIFECYCLE INTEGRATION TEST (STEP 43)
# ==============================================================================

def test_full_project_lifecycle_integration(review3_db):
    """
    STEP 43 — Complete Project Lifecycle Integration:
    Generate event -> Ingest -> Detect Lateness -> Identify Historical Report ->
    Calculate Delta -> Trigger High-Impact Review Queue -> Approve via Administrator ->
    Create Monotonic Report Version -> Create Immutable Audit Trail ->
    Reconcile Against Ground Truth -> Compensating Rollback -> Verify Final Consistent State.
    """
    session, engine = review3_db
    target_date = "2026-08-20"
    domain = "RTC-Attendance"

    # Step 1: Ingest On-Time Baseline Event
    e1 = {
        "event_id": "LIFECYCLE-EVT-01",
        "domain": domain,
        "student_id": "RTC-STU-0001",
        "event_timestamp": f"{target_date}T08:30:00",
        "arrival_timestamp": f"{target_date}T08:45:00", # On-time (15 min)
        "batch_id": "BATCH-LIFECYCLE-01",
        "payload": {"attendance_status": "Present", "class_id": "CS-101", "attendance_date": target_date}
    }
    r1 = ingest_and_process_atomic(session, e1)
    assert r1["status"] == "INGESTED"
    assert r1["is_late"] is False

    report = session.query(DailyReport).filter(
        DailyReport.reporting_date == target_date,
        DailyReport.domain == domain
    ).first()
    assert report is not None
    assert report.baseline_aggregate == 1.0
    assert report.corrected_aggregate == 1.0
    assert report.current_version == 2 # v1 initial (0.0) + v2 on-time update (1.0)

    # Step 2: Ingest Late Event with High-Impact Drift (96 hours late)
    e2_late = {
        "event_id": "LIFECYCLE-EVT-02",
        "domain": domain,
        "student_id": "RTC-STU-0002",
        "event_timestamp": f"{target_date}T08:30:00",
        "arrival_timestamp": "2026-08-24T08:30:00", # 96.0h late
        "batch_id": "BATCH-LIFECYCLE-02",
        "payload": {
            "attendance_status": "Present",
            "class_id": "CS-101",
            "attendance_date": target_date,
            "is_high_risk_outcome": True # Force review
        }
    }
    r2 = ingest_and_process_atomic(session, e2_late)
    assert r2["status"] == "INGESTED"
    assert r2["is_late"] is True

    corr_res = r2["correction_result"]
    assert corr_res["requires_review"] is True
    corr_id = corr_res["correction_id"]

    # Step 3: Verify Report Enters PENDING_REVIEW without modifying official aggregate prematurely
    session.refresh(report)
    assert report.status == "PENDING_REVIEW"
    assert report.corrected_aggregate == 1.0 # Still 1.0 until approved!

    # Step 4: Administrator Approves Correction
    app_res = review_pending_correction(
        session, 
        corr_id, 
        "APPROVE", 
        reviewer_name="Dr. K. Swaminathan (Dean)", 
        reason="Verified physical lab attendance register"
    )
    assert app_res["status"] == "APPROVED"
    assert app_res["aggregate"] == 2.0

    # Step 5: Verify Report Version v3 Created
    session.refresh(report)
    assert report.corrected_aggregate == 2.0
    assert report.current_version == 3

    v3 = session.query(ReportVersion).filter(
        ReportVersion.report_id == report.report_id,
        ReportVersion.version_number == 3
    ).first()
    assert v3 is not None
    assert v3.change_type == "REVIEW_APPROVAL"
    assert v3.aggregate_value == 2.0

    # Step 6: Verify Immutable Audit Trail Lineage
    audit_actions = [
        a.action for a in session.query(AuditLog).filter(
            AuditLog.domain == domain
        ).order_by(AuditLog.id.asc()).all()
    ]
    assert "INGEST_EVENT" in audit_actions
    assert "QUEUE_FOR_REVIEW" in audit_actions
    assert "APPROVE_CORRECTION" in audit_actions

    # Step 7: Reconcile Against Independent Ground Truth
    gt_val = compute_ground_truth(session, target_date, domain)
    assert report.corrected_aggregate == gt_val == 2.0

    # Step 8: Execute Compensating Rollback
    rb_res = execute_rollback(session, corr_id, reason="Administrative correction appeal")
    assert rb_res["status"] == "ROLLED_BACK"

    # Step 9: Verify Restored State & Monotonic Version v4
    session.refresh(report)
    assert report.corrected_aggregate == 1.0 # Reverted back to baseline
    assert report.current_version == 4       # History preserved via v4 append

    v4 = session.query(ReportVersion).filter(
        ReportVersion.report_id == report.report_id,
        ReportVersion.version_number == 4
    ).first()
    assert v4 is not None
    assert v4.change_type == "ROLLBACK"
    assert v4.aggregate_value == 1.0

    # Final Invariant: Prior versions remain completely preserved
    all_versions = session.query(ReportVersion).filter(
        ReportVersion.report_id == report.report_id
    ).order_by(ReportVersion.version_number.asc()).all()
    assert len(all_versions) == 4
    assert [v.version_number for v in all_versions] == [1, 2, 3, 4]
