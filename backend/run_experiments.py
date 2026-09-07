import json
from app.experiments import run_full_experiment_suite
from app.config import settings

if __name__ == "__main__":
    print(f"[RTC Experiments] Running data quality benchmark experiment suite (Seed={settings.SEED})...")
    results = run_full_experiment_suite(seed=settings.SEED)
    print(f"[RTC Experiments] Experiment suite completed. {len(results)} scenarios evaluated.")
    for r in results:
        print(f" - {r['scenario_name']}: Baseline MAE={r['baseline_mae']}, Corrected MAE={r['corrected_mae']}, Exact Match={r['exact_match_pct']}%")
