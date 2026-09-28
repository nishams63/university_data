import os
import tempfile
import sqlite3
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.pipeline import ingest_raw_event, ingest_and_process_atomic
from app.correction import process_and_apply_corrections, compute_ground_truth, review_pending_correction
from app.audit import execute_rollback
from app.models import DailyReport, ReportCorrection, ReportVersion, AuditLog, RawEvent

@pytest.fixture(scope="function")
def concurrent_db_engine():
    """
    Creates an isolated file-based SQLite database with real WAL mode,
    busy_timeout=10000, and foreign keys enabled across concurrent threads.
    """
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_concurrent.db")
    db_url = f"sqlite:///{db_path}"

    engine = create_engine(
        db_url,
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
    yield engine
    engine.dispose()
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

def test_concurrency_test_a_duplicate_race(concurrent_db_engine):
    """
    Test A — Duplicate Race:
    Send the SAME event simultaneously from 10 threads.
    Expected result:
    - Exactly one logical event stored
    - No double counting in aggregate
    - Deterministic duplicate handling (DUPLICATE status for race losers)
    - No corrupted aggregate
    """
    Session = sessionmaker(bind=concurrent_db_engine, autocommit=False, autoflush=False)
    target_date = "2026-08-20"
    event_data = {
        "event_id": "CONC-RACE-DUP-001",
        "domain": "RTC-Attendance",
        "student_id": "RTC-STU-0001",
        "event_timestamp": f"{target_date}T09:00:00",
        "arrival_timestamp": f"{target_date}T09:15:00",
        "batch_id": "BATCH-RACE",
        "payload": {"attendance_status": "Present", "class_id": "CS-301", "attendance_date": target_date}
    }

    num_threads = 10
    results = []

    def submit_event():
        db = Session()
        try:
            res = ingest_and_process_atomic(db, event_data)
            return res["status"]
        finally:
            db.close()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(submit_event) for _ in range(num_threads)]
        for f in as_completed(futures):
            results.append(f.result())

    # Exactly 1 INGESTED, exactly 9 DUPLICATE
    ingested_count = results.count("INGESTED")
    duplicate_count = results.count("DUPLICATE")

    assert ingested_count == 1, f"Expected 1 INGESTED, got {ingested_count}"
    assert duplicate_count == num_threads - 1, f"Expected {num_threads - 1} DUPLICATE, got {duplicate_count}"

    # Verify database state
    verify_db = Session()
    try:
        raw_count = verify_db.query(RawEvent).filter(RawEvent.event_id == "CONC-RACE-DUP-001").count()
        assert raw_count == 1, "Duplicate raw_events inserted into database!"

        report = verify_db.query(DailyReport).filter(
            DailyReport.reporting_date == target_date,
            DailyReport.domain == "RTC-Attendance"
        ).first()
        assert report is not None
        assert report.corrected_aggregate == 1.0, f"Expected aggregate 1.0, got {report.corrected_aggregate}"
    finally:
        verify_db.close()

def test_concurrency_test_b_concurrent_unique_events(concurrent_db_engine):
    """
    Test B — Concurrent Unique Events:
    Submit 20 different events concurrently across multiple threads.
    Verify:
    - All valid unique events persisted
    - Correct aggregate sum without lost updates
    - Zero database-lock crashes (WAL mode handling)
    """
    Session = sessionmaker(bind=concurrent_db_engine, autocommit=False, autoflush=False)
    target_date = "2026-08-20"
    num_events = 20

    events = [
        {
            "event_id": f"CONC-UNIQ-{i:03d}",
            "domain": "RTC-Attendance",
            "student_id": f"RTC-STU-{i:04d}",
            "event_timestamp": f"{target_date}T09:00:00",
            "arrival_timestamp": f"{target_date}T09:15:00",
            "batch_id": "BATCH-CONC-UNIQ",
            "payload": {"attendance_status": "Present", "class_id": "CS-301", "attendance_date": target_date}
        }
        for i in range(1, num_events + 1)
    ]

    def ingest_worker(evt):
        db = Session()
        try:
            res = ingest_and_process_atomic(db, evt)
            return res["status"]
        finally:
            db.close()

    with ThreadPoolExecutor(max_workers=8) as executor:
        statuses = list(executor.map(ingest_worker, events))

    assert all(s == "INGESTED" for s in statuses)

    verify_db = Session()
    try:
        raw_count = verify_db.query(RawEvent).filter(RawEvent.reporting_date == target_date).count()
        assert raw_count == num_events

        gt = compute_ground_truth(verify_db, target_date, "RTC-Attendance")
        assert gt == float(num_events)

        report = verify_db.query(DailyReport).filter(
            DailyReport.reporting_date == target_date,
            DailyReport.domain == "RTC-Attendance"
        ).first()
        assert report.corrected_aggregate == float(num_events)
    finally:
        verify_db.close()

def test_concurrency_test_c_concurrent_late_events_same_historical_date(concurrent_db_engine):
    """
    Test C — Concurrent Late Events for Same Historical Date:
    Seed an initial baseline, then concurrently submit 10 late events targeting that historical date.
    Verify:
    - Final corrected aggregate converges to independently calculated ground truth.
    - Zero corrupted versions or locked database errors.
    """
    Session = sessionmaker(bind=concurrent_db_engine, autocommit=False, autoflush=False)
    target_date = "2026-08-20"

    # Step 1: Initial on-time event
    init_db = Session()
    try:
        e_init = {
            "event_id": "CONC-LATE-INIT",
            "domain": "RTC-Attendance",
            "student_id": "RTC-STU-0001",
            "event_timestamp": f"{target_date}T09:00:00",
            "arrival_timestamp": f"{target_date}T09:15:00",
            "batch_id": "BATCH-INIT",
            "payload": {"attendance_status": "Present", "class_id": "CS-301", "attendance_date": target_date}
        }
        ingest_and_process_atomic(init_db, e_init)
    finally:
        init_db.close()

    # Step 2: Concurrently submit 10 late events (arriving 48 hours later)
    num_late = 10
    late_events = [
        {
            "event_id": f"CONC-LATE-{i:03d}",
            "domain": "RTC-Attendance",
            "student_id": f"RTC-STU-{(i+10):04d}",
            "event_timestamp": f"{target_date}T10:00:00",
            "arrival_timestamp": "2026-08-22T14:00:00", # 52 hours delay > 24h
            "batch_id": "BATCH-LATE-CONC",
            "payload": {"attendance_status": "Present", "class_id": "CS-301", "attendance_date": target_date}
        }
        for i in range(1, num_late + 1)
    ]

    def late_worker(evt):
        db = Session()
        try:
            return ingest_and_process_atomic(db, evt)
        finally:
            db.close()

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(late_worker, late_events))

    assert len(results) == num_late

    verify_db = Session()
    try:
        gt = compute_ground_truth(verify_db, target_date, "RTC-Attendance")
        # 1 init + 10 late = 11.0
        assert gt == 11.0

        report = verify_db.query(DailyReport).filter(
            DailyReport.reporting_date == target_date,
            DailyReport.domain == "RTC-Attendance"
        ).first()
        assert report.corrected_aggregate == 11.0, f"Expected 11.0, got {report.corrected_aggregate}"
        assert report.status == "CORRECTED"
    finally:
        verify_db.close()

def test_concurrency_test_d_concurrent_review_approval_protection(concurrent_db_engine):
    """
    Test D — Concurrent Review/Approval Protection:
    Attempt conflicting review operations (concurrent approvals and rejections) on the same correction.
    Ensure double approval does not corrupt report versions.
    """
    Session = sessionmaker(bind=concurrent_db_engine, autocommit=False, autoflush=False)
    target_date = "2026-08-20"

    # Ingest forced high-risk placement event
    init_db = Session()
    try:
        hi_evt = {
            "event_id": "CONC-REV-EVT-01",
            "domain": "RTC-Placement",
            "student_id": "RTC-STU-0099",
            "event_timestamp": f"{target_date}T11:00:00",
            "arrival_timestamp": "2026-08-23T15:00:00",
            "batch_id": "BATCH-REV-HI",
            "payload": {
                "drive_id": "DRIVE-GOOGLE",
                "offer_status": "Offered",
                "is_placement_status_change": True
            }
        }
        res = ingest_and_process_atomic(init_db, hi_evt)
        corr_id = res["correction_result"]["correction_id"]
    finally:
        init_db.close()

    # Attempt concurrent approvals and rejections on corr_id
    actions = ["APPROVE", "REJECT", "APPROVE", "REJECT"]
    results = []

    def review_worker(act):
        db = Session()
        try:
            return review_pending_correction(db, corr_id, act, reviewer_name="Concurrent Reviewer")
        finally:
            db.close()

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(review_worker, act) for act in actions]
        for f in as_completed(futures):
            results.append(f.result())

    # Exactly ONE action should succeed (either APPROVED or REJECTED); the rest must return status ERROR
    successful_actions = [r for r in results if r.get("status") in ["APPROVED", "REJECTED"]]
    error_actions = [r for r in results if r.get("status") == "ERROR"]

    assert len(successful_actions) == 1, f"Expected exactly 1 successful review action, got {len(successful_actions)}"
    assert len(error_actions) == len(actions) - 1, f"Expected {len(actions) - 1} rejections, got {len(error_actions)}"

    verify_db = Session()
    try:
        corr = verify_db.query(ReportCorrection).filter(ReportCorrection.correction_id == corr_id).first()
        assert corr.status in ["APPROVED", "REJECTED"]
    finally:
        verify_db.close()

def test_concurrency_test_e_rollback_idempotency(concurrent_db_engine):
    """
    Test E — Rollback Idempotency:
    Attempt repeated rollback calls concurrently across multiple threads.
    Verify: Exactly one logical compensating rollback takes effect,
    and subsequent calls return ALREADY_ROLLED_BACK without corrupting report versions.
    """
    Session = sessionmaker(bind=concurrent_db_engine, autocommit=False, autoflush=False)
    target_date = "2026-08-20"

    init_db = Session()
    try:
        e1 = {
            "event_id": "CONC-RBK-EVT-01",
            "domain": "RTC-Attendance",
            "student_id": "RTC-STU-0001",
            "event_timestamp": f"{target_date}T09:00:00",
            "arrival_timestamp": f"{target_date}T09:15:00",
            "batch_id": "BATCH-01",
            "payload": {"attendance_status": "Present", "class_id": "CS-301", "attendance_date": target_date}
        }
        ingest_and_process_atomic(init_db, e1)

        e2_late = {
            "event_id": "CONC-RBK-EVT-02",
            "domain": "RTC-Attendance",
            "student_id": "RTC-STU-0002",
            "event_timestamp": f"{target_date}T09:00:00",
            "arrival_timestamp": "2026-08-23T10:00:00",
            "batch_id": "BATCH-02",
            "payload": {"attendance_status": "Present", "class_id": "CS-301", "attendance_date": target_date}
        }
        res2 = ingest_and_process_atomic(init_db, e2_late)
        corr_id = res2["correction_result"]["correction_id"]
    finally:
        init_db.close()

    # Concurrently trigger rollback 6 times
    num_rollbacks = 6
    rb_results = []

    def rollback_worker():
        db = Session()
        try:
            return execute_rollback(db, corr_id, reason="Concurrent test rollback")
        finally:
            db.close()

    with ThreadPoolExecutor(max_workers=num_rollbacks) as executor:
        futures = [executor.submit(rollback_worker) for _ in range(num_rollbacks)]
        for f in as_completed(futures):
            rb_results.append(f.result())

    # Exactly 1 ROLLED_BACK, the rest ALREADY_ROLLED_BACK
    rolled_back_count = sum(1 for r in rb_results if r.get("status") == "ROLLED_BACK")
    already_count = sum(1 for r in rb_results if r.get("status") == "ALREADY_ROLLED_BACK")

    assert rolled_back_count == 1, f"Expected 1 ROLLED_BACK, got {rolled_back_count}"
    assert already_count == num_rollbacks - 1, f"Expected {num_rollbacks - 1} ALREADY_ROLLED_BACK, got {already_count}"

    verify_db = Session()
    try:
        report = verify_db.query(DailyReport).filter(
            DailyReport.reporting_date == target_date,
            DailyReport.domain == "RTC-Attendance"
        ).first()
        assert report.corrected_aggregate == 1.0, f"Expected restored aggregate 1.0, got {report.corrected_aggregate}"

        # Only one rollback version record should have been appended
        rollback_versions = verify_db.query(ReportVersion).filter(
            ReportVersion.report_id == report.report_id,
            ReportVersion.change_type == "ROLLBACK"
        ).all()
        assert len(rollback_versions) == 1, f"Expected 1 rollback version record, got {len(rollback_versions)}"
    finally:
        verify_db.close()
