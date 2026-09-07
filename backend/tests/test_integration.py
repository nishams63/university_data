import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.generator import generate_synthetic_event_stream
from app.pipeline import ingest_raw_event
from app.correction import process_and_apply_corrections, compute_ground_truth, review_pending_correction
from app.audit import execute_rollback
from app.models import DailyReport, ReportCorrection, AuditLog, RawEvent

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_full_end_to_end_integration_flow(db):
    """
    End-to-End Integration Test:
    Generate events -> Ingest -> Process -> Introduce late events -> Correct aggregates -> 
    Introduce duplicates -> Verify no double counting -> Inspect audit trail -> 
    Perform rollback -> Verify final invariant: CorrectedAggregate(D) == GroundTruth(D)
    """
    seed = 42
    students, events = generate_synthetic_event_stream(
        num_events=150,
        late_ratio=0.20,
        duplicate_ratio=0.10,
        invalid_ratio=0.04,
        seed=seed
    )

    ingested_cnt = 0
    duplicate_cnt = 0
    invalid_cnt = 0

    # Phase 1: Ingest & Process all events
    for evt in events:
        res = ingest_raw_event(db, evt)
        status = res["status"]
        if status == "INGESTED":
            ingested_cnt += 1
            proc_res = process_and_apply_corrections(db, res["event_id"])
            if proc_res.get("requires_review"):
                # Automatically approve pending reviews to complete event processing
                review_pending_correction(db, proc_res["correction_id"], "APPROVE")
        elif status == "DUPLICATE":
            duplicate_cnt += 1
        elif status == "INVALID":
            invalid_cnt += 1

    assert ingested_cnt > 0
    assert duplicate_cnt > 0
    assert invalid_cnt > 0

    # Phase 2: Invariant Check across all reporting dates and domains
    reports = db.query(DailyReport).all()
    assert len(reports) > 0

    for r in reports:
        gt = compute_ground_truth(db, r.reporting_date, r.domain)
        # CRITICAL INVARIANT: CorrectedAggregate(D) == GroundTruth(D) after all valid events processed
        assert r.corrected_aggregate == gt, f"Invariant failed for report {r.report_id}: Corrected ({r.corrected_aggregate}) != GroundTruth ({gt})"

    # Phase 3: Rollback test & verification
    corr = db.query(ReportCorrection).filter(ReportCorrection.status == "AUTO_CORRECTED").first()
    if corr:
        rb_res = execute_rollback(db, corr.correction_id, reason="Integration test rollback")
        assert rb_res["status"] == "ROLLED_BACK"

    # Phase 4: Verify audit log entries exist for all actions
    actions_found = set(r.action for r in db.query(AuditLog).all())
    assert "INGEST_EVENT" in actions_found
    assert "DISCARD_DUPLICATE" in actions_found
    assert "DISCARD_INVALID" in actions_found
    assert "APPLY_CORRECTION" in actions_found
