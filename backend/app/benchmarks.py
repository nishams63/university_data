import os
import time
import json
import tracemalloc
import statistics
import tempfile
import sqlite3
from datetime import datetime, timezone
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.generator import generate_synthetic_event_stream, generate_single_event
from app.pipeline import ingest_and_process_atomic
from app.correction import compute_ground_truth, review_pending_correction
from app.models import RawEvent, DailyReport, ReportCorrection

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "results")

def ensure_results_dir():
    os.makedirs(RESULTS_DIR, exist_ok=True)

def create_benchmark_engine():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "benchmark.db")
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
    return engine, db_path

def run_single_dataset_benchmark(num_events: int, seed: int = 42) -> dict:
    """
    Executes a real benchmark on `num_events` measuring actual timing and memory.
    """
    engine, db_path = create_benchmark_engine()
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = Session()

    students, events = generate_synthetic_event_stream(
        num_events=num_events,
        late_ratio=0.20,
        duplicate_ratio=0.08,
        invalid_ratio=0.02,
        seed=seed
    )

    tracemalloc.start()
    latencies_ms = []
    late_latencies_ms = []
    successful_ingest = 0
    duplicate_count = 0
    invalid_count = 0

    overall_start = time.perf_counter()

    for evt in events:
        t0 = time.perf_counter()
        res = ingest_and_process_atomic(db, evt)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(elapsed_ms)

        st = res["status"]
        if st == "INGESTED":
            successful_ingest += 1
            if res.get("is_late"):
                late_latencies_ms.append(elapsed_ms)
        elif st == "DUPLICATE":
            duplicate_count += 1
        elif st == "INVALID":
            invalid_count += 1

    overall_duration = time.perf_counter() - overall_start
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Reconcile pending reviews to measure reconciliation duration
    rec_start = time.perf_counter()
    pending = db.query(ReportCorrection).filter(ReportCorrection.status == "PENDING_REVIEW").all()
    for p in pending:
        review_pending_correction(db, p.correction_id, "APPROVE")

    reports = db.query(DailyReport).all()
    exact_matches = 0
    for r in reports:
        gt = compute_ground_truth(db, r.reporting_date, r.domain)
        if r.corrected_aggregate == gt:
            exact_matches += 1
    reconciliation_duration_ms = (time.perf_counter() - rec_start) * 1000.0

    # Calculate statistics
    latencies_ms.sort()
    avg_latency = statistics.mean(latencies_ms) if latencies_ms else 0.0
    median_latency = statistics.median(latencies_ms) if latencies_ms else 0.0
    p95_index = int(len(latencies_ms) * 0.95)
    p99_index = int(len(latencies_ms) * 0.99)
    p95_latency = latencies_ms[min(p95_index, len(latencies_ms) - 1)] if latencies_ms else 0.0
    p99_latency = latencies_ms[min(p99_index, len(latencies_ms) - 1)] if latencies_ms else 0.0
    events_per_sec = len(events) / overall_duration if overall_duration > 0 else 0.0

    avg_late_latency = statistics.mean(late_latencies_ms) if late_latencies_ms else avg_latency

    db_size_bytes = os.path.getsize(db_path) if os.path.exists(db_path) else 0

    db.close()
    engine.dispose()
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

    return {
        "event_count": len(events),
        "duration_seconds": round(overall_duration, 4),
        "events_per_second": round(events_per_sec, 2),
        "avg_latency_ms": round(avg_latency, 3),
        "median_latency_ms": round(median_latency, 3),
        "p95_latency_ms": round(p95_latency, 3),
        "p99_latency_ms": round(p99_latency, 3),
        "late_correction_avg_latency_ms": round(avg_late_latency, 3),
        "reconciliation_duration_ms": round(reconciliation_duration_ms, 2),
        "peak_memory_mb": round(peak_mem / (1024 * 1024), 3),
        "database_size_kb": round(db_size_bytes / 1024, 2),
        "successful_ingest_count": successful_ingest,
        "duplicate_discard_count": duplicate_count,
        "invalid_discard_count": invalid_count,
        "exact_match_percentage": round((exact_matches / max(len(reports), 1)) * 100.0, 1)
    }

def run_historical_replay_benchmark(seed: int = 42) -> dict:
    """
    Executes historical replay across 4 representative workload profiles (1000 events each):
    1. Normal Ingestion (10% late)
    2. Late-Event-Heavy (40% late)
    3. Duplicate-Heavy (15% late, 30% duplicate)
    4. 7-Day Delayed Lag (35% late with 72-168h delays)
    """
    engine, db_path = create_benchmark_engine()
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = Session()

    scenarios = [
        {"profile": "Normal Institutional Stream", "late": 0.10, "dup": 0.03, "inv": 0.01},
        {"profile": "Late-Event-Heavy Stream", "late": 0.40, "dup": 0.05, "inv": 0.02},
        {"profile": "Duplicate-Heavy Stream", "late": 0.15, "dup": 0.30, "inv": 0.02},
        {"profile": "7-Day Delayed Ingestion Lag", "late": 0.35, "dup": 0.08, "inv": 0.03}
    ]

    replay_results = []
    total_replay_events = 0
    total_replay_time = 0.0

    for sc in scenarios:
        students, events = generate_synthetic_event_stream(
            num_events=1000,
            late_ratio=sc["late"],
            duplicate_ratio=sc["dup"],
            invalid_ratio=sc["inv"],
            seed=seed
        )

        tracemalloc.start()
        t0 = time.perf_counter()
        latencies = []
        for evt in events:
            evt_t0 = time.perf_counter()
            ingest_and_process_atomic(db, evt)
            latencies.append((time.perf_counter() - evt_t0) * 1000.0)

        duration = time.perf_counter() - t0
        _, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        latencies.sort()
        avg_lat = statistics.mean(latencies)
        p95_lat = latencies[int(len(latencies) * 0.95)]
        eps = len(events) / duration if duration > 0 else 0.0

        total_replay_events += len(events)
        total_replay_time += duration

        replay_results.append({
            "profile": sc["profile"],
            "events_replayed": len(events),
            "duration_seconds": round(duration, 3),
            "events_per_second": round(eps, 2),
            "avg_latency_ms": round(avg_lat, 3),
            "p95_latency_ms": round(p95_lat, 3),
            "peak_memory_mb": round(peak_mem / (1024 * 1024), 3)
        })

    overall_replay_eps = total_replay_events / total_replay_time if total_replay_time > 0 else 0.0

    db.close()
    engine.dispose()
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

    return {
        "total_replay_events": total_replay_events,
        "total_replay_duration_seconds": round(total_replay_time, 3),
        "overall_replay_throughput_eps": round(overall_replay_eps, 2),
        "profiles": replay_results
    }

def run_full_benchmark_suite(seed: int = 42) -> dict:
    """
    Executes both event scaling benchmarks (100, 500, 1000, 5000 events)
    and historical replay benchmark, persisting results to disk.
    """
    ensure_results_dir()
    print("[RTC Benchmark] Running event scaling benchmarks (100, 500, 1000, 5000 events)...")
    
    scaling_counts = [100, 500, 1000, 5000]
    scaling_results = []

    for cnt in scaling_counts:
        print(f"  -> Benchmarking {cnt} events...")
        res = run_single_dataset_benchmark(cnt, seed=seed)
        scaling_results.append(res)
        print(f"     Done: {res['events_per_second']} eps, avg {res['avg_latency_ms']} ms, peak RAM {res['peak_memory_mb']} MB")

    print("[RTC Benchmark] Running historical replay benchmarks (4 profiles x 1000 events)...")
    replay_summary = run_historical_replay_benchmark(seed=seed)
    print(f"  -> Replay Completed: {replay_summary['overall_replay_throughput_eps']} eps overall throughput.")

    full_output = {
        "benchmark_timestamp": datetime.now(timezone.utc).isoformat(),
        "institution": "RATHINAM TECHNICAL CAMPUS (AUTONOMOUS)",
        "environment": {
            "database_engine": "SQLite 3 with Write-Ahead Logging (WAL)",
            "journal_mode": "wal",
            "busy_timeout_ms": 10000,
            "synchronous_mode": "NORMAL",
            "concurrency_model": "Multi-threaded with atomic transaction boundaries and monotonic versioning"
        },
        "event_scaling_benchmarks": scaling_results,
        "historical_replay_benchmark": replay_summary
    }

    output_path = os.path.join(RESULTS_DIR, "performance_benchmark.json")
    with open(output_path, "w") as f:
        json.dump(full_output, f, indent=2)

    print(f"[RTC Benchmark] Results saved to {output_path}")
    return full_output
