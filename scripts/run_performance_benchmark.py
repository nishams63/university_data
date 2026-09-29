#!/usr/bin/env python3
"""
Performance Benchmark CLI Engine
Rathinam Technical Campus (Autonomous), Coimbatore
Evaluates throughput, latency percentiles, memory consumption, and historical replay.
"""
import sys
import os
import argparse

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from app.benchmarks import run_full_benchmark_suite, run_single_dataset_benchmark, run_historical_replay_benchmark

def main():
    parser = argparse.ArgumentParser(description="RTC Real Benchmark Engine for Late-Event Correction System")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--full", action="store_true", default=True, help="Run complete scaling and historical replay suite")
    parser.add_argument("--quick", action="store_true", help="Run quick benchmark on 100 and 500 events only")
    args = parser.parse_args()

    print("================================================================================")
    print("  RATHINAM TECHNICAL CAMPUS (AUTONOMOUS) — PERFORMANCE BENCHMARK ENGINE")
    print("  A Stateful Watermark and Delta Recalculation Engine for Institutional Big Data")
    print(f"  Configuration: Seed={args.seed} | Mode={'Quick' if args.quick else 'Full Suite'}")
    print("================================================================================\n")

    if args.quick:
        print("[RTC Benchmark] Executing Quick Verification Benchmark (100, 500 events)...")
        res100 = run_single_dataset_benchmark(100, seed=args.seed)
        res500 = run_single_dataset_benchmark(500, seed=args.seed)
        for res in [res100, res500]:
            print(f"Count: {res['event_count']:5d} | Duration: {res['duration_seconds']:6.2f}s | "
                  f"Throughput: {res['events_per_second']:7.2f} eps | Avg Lat: {res['avg_latency_ms']:6.2f}ms | "
                  f"Min: {res['min_latency_ms']:6.2f}ms | Max: {res['max_latency_ms']:6.2f}ms | "
                  f"P95: {res['p95_latency_ms']:6.2f}ms | P99: {res['p99_latency_ms']:6.2f}ms | "
                  f"RAM: {res['peak_memory_mb']:5.2f} MB | DB: {res['database_size_kb']:7.1f} KB")
        return

    results = run_full_benchmark_suite(seed=args.seed)

    print("\n================================================================================")
    print("  FINAL MEASURED PERFORMANCE BENCHMARK RESULTS")
    print("================================================================================")
    print(f"{'Events':<8} | {'Duration':<9} | {'Throughput':<12} | {'Avg Lat':<9} | {'Min Lat':<9} | {'Max Lat':<9} | {'P95 Lat':<9} | {'P99 Lat':<9} | {'Peak RAM':<9} | {'DB Size':<10}")
    print("-" * 115)
    for b in results["event_scaling_benchmarks"]:
        print(f"{b['event_count']:<8d} | {b['duration_seconds']:<7.2f}s | {b['events_per_second']:<8.2f} eps | "
              f"{b['avg_latency_ms']:<7.2f}ms | {b.get('min_latency_ms', 0.0):<7.2f}ms | {b.get('max_latency_ms', 0.0):<7.2f}ms | "
              f"{b['p95_latency_ms']:<7.2f}ms | {b['p99_latency_ms']:<7.2f}ms | {b['peak_memory_mb']:<7.2f}MB | {b['database_size_kb']:<8.1f}KB")

    replay = results["historical_replay_benchmark"]
    print("\n================================================================================")
    print(f"  HISTORICAL REPLAY BENCHMARK (Total: {replay['total_replay_events']} events, Duration: {replay['total_replay_duration_seconds']}s, Overall Throughput: {replay['overall_replay_throughput_eps']} eps)")
    print("================================================================================")
    for p in replay["profiles"]:
        print(f"  * {p['profile']:<32} -> {p['events_replayed']:4d} events in {p['duration_seconds']:6.2f}s ({p['events_per_second']:7.2f} eps, P95: {p['p95_latency_ms']:6.2f}ms, RAM: {p['peak_memory_mb']:5.2f} MB)")
    print("================================================================================\n")

if __name__ == "__main__":
    main()
