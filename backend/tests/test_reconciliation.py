import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.generator import generate_synthetic_event_stream
from app.pipeline import ingest_raw_event
from app.correction import process_and_apply_corrections, compute_ground_truth, review_pending_correction
from app.models import DailyReport, ReportCorrection, RawEvent

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_final_corrected_aggregate_equals_ground_truth(db):
    """
    Mandatory Reconciliation Test (Requirement 8):
    After all valid events for the experiment have arrived and been processed (and all reviews validated),
    assert CorrectedAggregate(D) == GroundTruth(D) for EVERY reporting date D.
    If it fails, show the exact mismatching date, domain, and event IDs.
    """
    seed = 42
    students, events = generate_synthetic_event_stream(
        num_events=300,
        late_ratio=0.25,
        duplicate_ratio=0.10,
        invalid_ratio=0.03,
        seed=seed
    )

    # Ingest and process all events
    for evt in events:
        res = ingest_raw_event(db, evt)
        if res["status"] == "INGESTED":
            process_and_apply_corrections(db, res["event_id"])

    # Reconcile pending review queue to finalize validated aggregates
    pending_reviews = db.query(ReportCorrection).filter(ReportCorrection.status == "PENDING_REVIEW").all()
    for pr in pending_reviews:
        review_pending_correction(db, pr.correction_id, "APPROVE")

    # Assert invariant across ALL daily reports
    reports = db.query(DailyReport).all()
    assert len(reports) > 0, "No daily reports were generated during test"

    mismatches = []
    for r in reports:
        gt = compute_ground_truth(db, r.reporting_date, r.domain)
        corr = r.corrected_aggregate
        if corr != gt:
            # Gather contributing event IDs
            evts = db.query(RawEvent).filter(
                RawEvent.reporting_date == r.reporting_date,
                RawEvent.domain == r.domain,
                RawEvent.is_valid == True
            ).all()
            evt_ids = [e.event_id for e in evts]
            mismatches.append({
                "date": r.reporting_date,
                "domain": r.domain,
                "corrected": corr,
                "ground_truth": gt,
                "error": abs(corr - gt),
                "event_ids": evt_ids
            })

    assert len(mismatches) == 0, f"Reconciliation invariant failed on {len(mismatches)} report dates: {mismatches}"
