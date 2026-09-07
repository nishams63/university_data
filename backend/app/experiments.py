import os
import json
import time
import math
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.generator import generate_synthetic_event_stream
from app.pipeline import ingest_raw_event
from app.correction import process_and_apply_corrections, compute_ground_truth, compute_naive_baseline, review_pending_correction
from app.models import ExperimentResult, DailyReport, RawEvent, ReportCorrection
from app.database import Base

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "results")

def ensure_results_dir():
    os.makedirs(RESULTS_DIR, exist_ok=True)

def run_single_experiment_scenario(
    scenario_name: str,
    late_ratio: float,
    duplicate_ratio: float,
    invalid_ratio: float,
    seed: int = 42,
    num_events: int = 200
) -> dict:
    start_time = time.time()
    
    # Use clean isolated in-memory database engine for exact reproducibility and zero lock conflict
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    Session = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    db = Session()

    try:
        # Generate synthetic stream
        students, events = generate_synthetic_event_stream(
            num_events=num_events,
            late_ratio=late_ratio,
            duplicate_ratio=duplicate_ratio,
            invalid_ratio=invalid_ratio,
            seed=seed
        )

        on_time_cnt = 0
        late_cnt = 0
        dup_cnt = 0
        inv_cnt = 0

        # Ingest and process all events in sequence
        for evt in events:
            res = ingest_raw_event(db, evt)
            status = res["status"]
            if status == "DUPLICATE":
                dup_cnt += 1
            elif status == "INVALID":
                inv_cnt += 1
            elif status == "INGESTED":
                if res["is_late"]:
                    late_cnt += 1
                else:
                    on_time_cnt += 1
                # Process correction
                process_and_apply_corrections(db, res["event_id"])

        proc_time_ms = round((time.time() - start_time) * 1000.0, 2)

        # Reconcile & approve all pending reviews after all events have arrived for final validated report evaluation
        pending_reviews = db.query(ReportCorrection).filter(ReportCorrection.status == "PENDING_REVIEW").all()
        for pr in pending_reviews:
            review_pending_correction(db, pr.correction_id, "APPROVE")

        # Calculate metrics across all daily reports generated
        reports = db.query(DailyReport).all()
        
        baseline_errors = []
        corrected_errors = []
        exact_matches = 0
        total_reports = len(reports) or 1

        for r in reports:
            gt = compute_ground_truth(db, r.reporting_date, r.domain)
            base_val = compute_naive_baseline(db, r.reporting_date, r.domain)
            corr_val = r.corrected_aggregate

            b_err = abs(base_val - gt)
            c_err = abs(corr_val - gt)

            baseline_errors.append(b_err)
            corrected_errors.append(c_err)

            if corr_val == gt:
                exact_matches += 1

        baseline_mae = round(sum(baseline_errors) / len(baseline_errors), 4) if baseline_errors else 0.0
        corrected_mae = round(sum(corrected_errors) / len(corrected_errors), 4) if corrected_errors else 0.0

        baseline_rmse = round(math.sqrt(sum(e**2 for e in baseline_errors) / len(baseline_errors)), 4) if baseline_errors else 0.0
        corrected_rmse = round(math.sqrt(sum(e**2 for e in corrected_errors) / len(corrected_errors)), 4) if corrected_errors else 0.0

        exact_match_pct = round((exact_matches / total_reports) * 100.0, 2)

        return {
            "experiment_id": f"EXP-{seed}-{scenario_name.upper().replace(' ', '_').replace(':', '')}",
            "scenario_name": scenario_name,
            "late_event_ratio": late_ratio,
            "total_events": len(events),
            "on_time_events_count": on_time_cnt,
            "late_events_count": late_cnt,
            "duplicate_events_count": dup_cnt,
            "invalid_events_count": inv_cnt,
            "baseline_mae": baseline_mae,
            "corrected_mae": corrected_mae,
            "baseline_rmse": baseline_rmse,
            "corrected_rmse": corrected_rmse,
            "exact_match_pct": exact_match_pct,
            "processing_time_ms": proc_time_ms,
            "created_at": datetime.utcnow().isoformat()
        }
    finally:
        db.close()
        test_engine.dispose()

def run_full_experiment_suite(seed: int = 42) -> list[dict]:
    ensure_results_dir()
    
    scenarios = [
        {"name": "Scenario 1: 0% Late Events", "late": 0.0, "dup": 0.0, "inv": 0.0},
        {"name": "Scenario 2: 5% Late Events", "late": 0.05, "dup": 0.01, "inv": 0.0},
        {"name": "Scenario 3: 10% Late Events", "late": 0.10, "dup": 0.02, "inv": 0.01},
        {"name": "Scenario 4: 25% Late Events", "late": 0.25, "dup": 0.03, "inv": 0.02},
        {"name": "Scenario 5: Duplicate Events", "late": 0.15, "dup": 0.15, "inv": 0.02},
        {"name": "Scenario 6: Very Late Events", "late": 0.30, "dup": 0.05, "inv": 0.05},
    ]

    all_results = []
    
    for sc in scenarios:
        res = run_single_experiment_scenario(
            scenario_name=sc["name"],
            late_ratio=sc["late"],
            duplicate_ratio=sc["dup"],
            invalid_ratio=sc["inv"],
            seed=seed,
            num_events=200
        )
        all_results.append(res)

    # Save summary json artifact to data/results/experiment_summary.json
    summary_path = os.path.join(RESULTS_DIR, "experiment_summary.json")
    with open(summary_path, "w") as f:
        json.dump(all_results, f, indent=2)

    return all_results
