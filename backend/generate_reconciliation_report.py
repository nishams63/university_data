import os
import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.generator import generate_synthetic_event_stream
from app.pipeline import ingest_raw_event
from app.correction import process_and_apply_corrections, compute_ground_truth, compute_naive_baseline, review_pending_correction
from app.models import DailyReport, ReportCorrection, RawEvent
from app.database import Base

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "results")

def generate_reconciliation_report():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Run full stream with late events, duplicates, and invalid payloads
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    Session = sessionmaker(bind=test_engine)
    db = Session()

    try:
        students, events = generate_synthetic_event_stream(
            num_events=300,
            late_ratio=0.25,
            duplicate_ratio=0.10,
            invalid_ratio=0.03,
            seed=42
        )

        for evt in events:
            res = ingest_raw_event(db, evt)
            if res["status"] == "INGESTED":
                process_and_apply_corrections(db, res["event_id"])

        # Reconcile pending review queue to finalize validated aggregates
        pending_reviews = db.query(ReportCorrection).filter(ReportCorrection.status == "PENDING_REVIEW").all()
        for pr in pending_reviews:
            review_pending_correction(db, pr.correction_id, "APPROVE")

        reports = db.query(DailyReport).all()
        total_dates = len(reports)
        matching_dates = 0
        mismatching_dates = 0
        total_abs_error = 0.0
        mismatches_list = []

        for r in reports:
            gt = compute_ground_truth(db, r.reporting_date, r.domain)
            corr = r.corrected_aggregate
            err = round(abs(corr - gt), 4)
            total_abs_error += err

            if err == 0.0:
                matching_dates += 1
            else:
                mismatching_dates += 1
                evts = db.query(RawEvent).filter(
                    RawEvent.reporting_date == r.reporting_date,
                    RawEvent.domain == r.domain,
                    RawEvent.is_valid == True
                ).all()
                mismatches_list.append({
                    "reporting_date": r.reporting_date,
                    "domain": r.domain,
                    "ground_truth": gt,
                    "corrected": corr,
                    "baseline": r.baseline_aggregate,
                    "error": err,
                    "event_ids": [e.event_id for e in evts]
                })

        exact_match_pct = round((matching_dates / max(total_dates, 1)) * 100.0, 2)

        report_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "institution": "RATHINAM TECHNICAL CAMPUS",
            "seed": 42,
            "total_reporting_dates": total_dates,
            "matching_dates": matching_dates,
            "mismatching_dates": mismatching_dates,
            "exact_match_percentage": exact_match_pct,
            "total_absolute_error": round(total_abs_error, 4),
            "invariant_satisfied": mismatching_dates == 0,
            "mismatches": mismatches_list
        }

        report_path = os.path.join(RESULTS_DIR, "reconciliation_report.json")
        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2)

        print(f"[RTC Reconciliation] Saved reconciliation report to {report_path}")
        print(f" - Total Reporting Dates: {total_dates}")
        print(f" - Matching Dates: {matching_dates}")
        print(f" - Mismatching Dates: {mismatching_dates}")
        print(f" - Exact Match Percentage: {exact_match_pct}%")
        print(f" - Invariant Satisfied: {report_data['invariant_satisfied']}")

        return report_data
    finally:
        db.close()
        test_engine.dispose()

if __name__ == "__main__":
    generate_reconciliation_report()
