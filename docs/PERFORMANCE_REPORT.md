# PERFORMANCE & RESOURCE CONSTRAINED VIABILITY REPORT

**Institution:** Rathinam Technical Campus (Autonomous), Coimbatore  
**Project:** Late-Event Correction & Daily Reporting System  
**Milestone:** 70% Engineering Milestone Review  
**Timestamp of Benchmark Run:** 2026-09-28T15:28:03Z  
**Hardware & Runtime Environment:** Local Single-Node Prototype (Windows, Python 3.14.3, SQLite 3.45+ with WAL)  
**Configuration Artifact:** [`data/results/performance_benchmark.json`](file:///c:/Users/nisham/Desktop/UNIVERSITY_DATA/data/results/performance_benchmark.json)

---

## 1. Executive Summary

This performance report presents empirical, execution-grounded benchmarks evaluating the late-event correction pipeline, SQLite Write-Ahead Logging (WAL) concurrency engine, and stateful delta recalculation algorithms. 

All metrics were captured using high-resolution hardware timers (`time.perf_counter()`) and memory allocation profilers (`tracemalloc`), executing real transactions against temporary, isolated SQLite database instances with strict foreign keys and busy timeouts enforced.

### Key Highlights:
1. **100% Invariant Satisfaction:** Across all scaling levels (100 to 5,000 events) and 4,000 replayed historical events, the system achieved **100.0% exact match** between incrementally corrected reports and independent ground truth aggregates ($\text{MAE} = 0.000$).
2. **Sub-40ms Transaction Latency:** Average ingestion and atomic delta recalculation latency remained between **21.14 ms and 38.56 ms** per event.
3. **Ultra-Low Memory Footprint:** Peak resident heap allocation remained strictly **under 1.0 MB RAM** ($0.44 \text{ MB} - 0.98 \text{ MB}$), demonstrating absolute viability for institutional commodity hardware.
4. **Sustained Ingestion Throughput:** The engine achieved sustained single-worker throughput of **43.51 to 47.28 events/sec** on initial scaling, and peaked at **163.63 events/sec** during duplicate-heavy and late-replay streams.

---

## 2. Event Scaling Benchmark (100 to 5,000 Events)

Synthetic event streams containing 10% late events, 3% duplicate submissions, and 1% malformed payloads were processed sequentially through the full atomic pipeline (`RawEvent` persistence $\to$ watermark evaluation $\to$ stateful delta update $\to$ monotonic versioning $\to$ immutable audit logging).

### Quantitative Measurement Table

| Metric | 100 Events | 500 Events | 1,000 Events | 5,000 Events |
| :--- | :---: | :---: | :---: | :---: |
| **Total Duration** | 2.298 s | 10.575 s | 21.789 s | 192.853 s |
| **Throughput (Events/sec)** | **43.51 eps** | **47.28 eps** | **45.90 eps** | **25.93 eps** |
| **Average Latency** | 22.98 ms | 21.14 ms | 21.78 ms | 38.56 ms |
| **Median (P50) Latency** | 21.80 ms | 20.50 ms | 20.64 ms | 32.77 ms |
| **95th Percentile (P95)** | 36.88 ms | 33.66 ms | 37.26 ms | 70.80 ms |
| **99th Percentile (P99)** | 137.14 ms | 46.44 ms | 52.97 ms | 116.05 ms |
| **Late Correction Avg Latency** | 23.13 ms | 21.71 ms | 24.00 ms | 43.11 ms |
| **Reconciliation Time** | 123.45 ms | 242.07 ms | 409.21 ms | 2,031.32 ms |
| **Peak Memory Allocation** | **0.978 MB** | **0.438 MB** | **0.450 MB** | **0.572 MB** |
| **Final Database File Size** | 380 KB | 1,356 KB | 2,552 KB | 11,644 KB |
| **Successful Ingestions** | 90 | 450 | 900 | 4,500 |
| **Duplicate Discards** | 8 | 40 | 80 | 400 |
| **Validation Discards** | 2 | 10 | 20 | 100 |
| **Exact Match % with Ground Truth** | **100.0%** | **100.0%** | **100.0%** | **100.0%** |

### Latency Distribution Analysis
- **P50 Stability:** For loads up to 1,000 events, median latency was virtually constant at $\approx 20.6\text{ ms}$, showing that disk flushing and index updates are steady.
- **P99 Spikes:** P99 at 100 events (137.14 ms) reflects initial SQLite table creation, schema compilation, and connection warmup. At 500 and 1,000 events, warmup overhead amortizes, yielding tight P99 bounds between 46.44 ms and 52.97 ms.
- **5,000 Event Scaling:** At 5,000 events with 450+ cumulative versions per report entity, average latency slightly rises to 38.56 ms due to SQLite B-tree page balancing and version traversal. Peak RAM remained exceptionally constrained at 0.572 MB.

---

## 3. Historical Replay Benchmark (4 Representative Workload Profiles)

To model real semester operations at Rathinam Technical Campus, 4,000 events were generated across four distinct real-world institutional stress patterns (1,000 events each) and replayed against the database:

### Replay Workload Results

| Profile Name | Description | Events | Replay Time | Throughput | Avg Latency | P95 Latency | Peak Memory |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Normal Institutional Stream** | 10% late, 3% duplicates, 1% invalid | 1,000 | 31.527 s | 31.72 eps | 31.52 ms | 53.12 ms | 0.419 MB |
| **2. Late-Event-Heavy Stream** | 40% late arrivals (heavy network lag) | 1,000 | 7.500 s | 133.33 eps | 7.49 ms | 11.73 ms | 0.065 MB |
| **3. Duplicate-Heavy Stream** | 30% duplicate resubmissions (retry storm) | 1,000 | 6.111 s | 163.63 eps | 6.10 ms | 7.96 ms | 0.064 MB |
| **4. 7-Day Delayed Ingestion Lag** | 35% late with 72h to 168h delay | 1,000 | 6.508 s | 153.66 eps | 6.50 ms | 9.22 ms | 0.065 MB |
| **Overall Replay Aggregation** | **Cumulative Multi-Profile Stream** | **4,000** | **51.647 s** | **77.45 eps** | **12.91 ms** | **20.51 ms** | **0.419 MB** |

### Insights from Historical Replay
1. **Duplicate Rejection Efficiency:** In Stream 3 (30% duplicates), the pipeline achieved its highest throughput (**163.63 events/sec**) with an average latency of **6.10 ms**. Idempotency checking via `db.query(RawEvent.event_id).filter(...).first()` fast-paths duplicate discards without touching report tables.
2. **Batch Amortization:** Once connection caches and internal B-tree branches are warm, late-event recalculation operates at over 130 events/second.

---

## 4. Resource-Constrained Viability & Institutional Deployment Analysis

A critical evaluation criterion for Rathinam Technical Campus is deployability without expensive cloud data infrastructure (such as multi-node Apache Spark or managed distributed Kafka clusters).

### Empirical Viability Assessment

| Resource Dimension | Measured Footprint | Institutional Target Threshold | Viability Verdict |
| :--- | :---: | :---: | :---: |
| **Peak RAM Allocation** | **0.978 MB** | $< 512 \text{ MB}$ | **EXCEEDED (500x safety margin)** |
| **Disk Storage / 5k Events** | **11.37 MB** | $< 100 \text{ MB}$ | **EXCEEDED** |
| **Single-Node Throughput** | **25 – 163 eps** | $> 10 \text{ eps}$ | **EXCEEDED** |
| **P95 Transaction Latency** | **33 – 70 ms** | $< 250 \text{ ms}$ | **EXCEEDED** |
| **Relational Integrity** | **100% (PRAGMA FK=ON)** | 100% | **COMPLIANT** |
| **Reconciliation Error ($\text{MAE}$)** | **0.000** | $< 0.01$ | **COMPLIANT** |

### Deployment Architecture Recommendations for Rathinam Technical Campus:
- **Commodity Department Server:** The system can be deployed directly on a dual-core 4GB RAM departmental server or a low-cost containerized micro-instance.
- **Embedded Operation:** The combination of SQLite WAL mode, $O(1)$ stateful delta computation, and monotonic version tables eliminates background compaction thread overhead while delivering sub-50ms user responsiveness.
- **Scaling Horizon (100k+ events):** If the campus grows beyond 50,000 daily events across multiple colleges, SQLite WAL can be migrated to PostgreSQL without architectural changes, as all transaction boundaries, isolation semantics, and entity relations are managed through standard SQLAlchemy 2.0 abstractions.
