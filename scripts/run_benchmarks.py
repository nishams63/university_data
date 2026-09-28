#!/usr/bin/env python3
"""
CLI script to run the performance benchmark engine for Rathinam Technical Campus.
Generates performance metrics across scaling datasets and historical replay scenarios.
"""
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from app.benchmarks import run_full_benchmark_suite

if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42
    print(f"Starting RTC Performance Benchmark Suite (Seed={seed})...")
    results = run_full_benchmark_suite(seed=seed)
    print("\n=== SUMMARY RESULTS ===")
    for b in results["event_scaling_benchmarks"]:
        print(f"Events: {b['event_count']:5d} | Dur: {b['duration_seconds']:6.2f}s | Throughput: {b['events_per_second']:7.2f} eps | Avg Lat: {b['avg_latency_ms']:6.2f}ms | P95: {b['p95_latency_ms']:6.2f}ms | P99: {b['p99_latency_ms']:6.2f}ms | RAM: {b['peak_memory_mb']:5.2f} MB")
    print(f"Replay Overall Throughput: {results['historical_replay_benchmark']['overall_replay_throughput_eps']} eps")
