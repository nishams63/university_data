# CAPSTONE PROJECT 70% MILESTONE REPORT

**Institution:** Rathinam Technical Campus (Autonomous), Coimbatore — 641 021  
**Department:** Computer Science and Engineering / Information Technology  
**Project Title:** Late-Event Correction & Daily Reporting System: A Stateful Watermark and Delta Recalculation Engine for Institutional Big Data  
**Review Stage:** 70% Engineering Milestone Review  
**Candidate / Repository:** [nishams63/university_data](https://github.com/nishams63/university_data)  
**Date of Submission:** September 2026  

---

## 1. Abstract

Institutional decision-making across higher education institutions relies heavily on daily operational indicators spanning classroom attendance, continuous internal assessments, digital LMS engagement, and campus placement drives. However, distributed edge sources—such as offline RFID turnstiles, network-delayed classroom portals, and manual exam score entries—inevitably introduce late-arriving events. In traditional Management Information Systems (MIS), these out-of-order events either corrupt the current day’s aggregates or are dropped, producing distorted institutional compliance metrics.

This project implements a **Stateful Watermark and Delta Recalculation Engine** specifically designed for Rathinam Technical Campus. The system enforces a dynamic 24-hour watermark window, extracts incremental state contributions in $O(1)$ time, bumps report versions monotonically, maintains an immutable write-only audit trail, and gates high-impact alterations (relative impact $\ge 15\%$ or grade flips) through a human-in-the-loop review workflow.

At this 70% milestone, the engine has transitioned from an initial 35% architectural proof-of-concept into a hardened, concurrency-tested, and empirically benchmarked engineering prototype. All 23 automated test suites pass cleanly, experimental evaluation across 6 distinct stress scenarios proves a $0.000$ Mean Absolute Error ($\text{MAE}$) against ground truth, and comprehensive benchmarks demonstrate single-worker throughput up to 163.6 events/second with a resident memory footprint strictly under 1.0 MB RAM.

---

## 2. Resolution of Prior Evaluator Criticisms (35% $\to$ 70% Transformation)

During the preliminary 35% evaluation, the review committee identified several architectural and experimental deficiencies. The table below details how each criticism was resolved:

| Prior Evaluator Criticism | Root Cause in 35% Baseline | Concrete Engineering Resolution at 70% | Verification Artifact |
| :--- | :--- | :--- | :--- |
| **1. "Database schema lacks concurrency controls, foreign key enforcement, and uniqueness constraints."** | Default SQLite rollback journal mode; no foreign key PRAGMA; composite keys unenforced; potential race conditions under concurrent writes. | Integrated connection-level PRAGMAs: `journal_mode=WAL`, `busy_timeout=10000`, `foreign_keys=ON`, `synchronous=NORMAL`. Added composite unique constraints `(reporting_date, domain)` and `(report_id, version_number)`. Developed multi-threaded concurrency test suite (`backend/tests/test_concurrency.py`). | [`docs/DATABASE_DESIGN.md`](file:///c:/Users/nisham/Desktop/UNIVERSITY_DATA/docs/DATABASE_DESIGN.md)<br>5/5 Concurrency Tests Passing |
| **2. "Performance claims are theoretical; lack execution-based scaling benchmarks and memory profiling."** | No actual automated benchmarking script; lack of hardware-timed latency percentiles or heap memory measurements. | Implemented `backend/app/benchmarks.py` using `time.perf_counter()` and `tracemalloc`. Executed scaling benchmarks (100, 500, 1000, 5000 events) and 4 historical replay profiles (4000 events total), capturing P50, P95, P99, throughput, and peak RAM. | [`docs/PERFORMANCE_REPORT.md`](file:///c:/Users/nisham/Desktop/UNIVERSITY_DATA/docs/PERFORMANCE_REPORT.md)<br>[`data/results/performance_benchmark.json`](file:///c:/Users/nisham/Desktop/UNIVERSITY_DATA/data/results/performance_benchmark.json) |
| **3. "Ingestion, delta recalculation, and versioning lacked strict transactional atomicity."** | Operations executed across fragmented queries; risk of orphaned reports if server crashed midway. | Built `ingest_and_process_atomic()` wrapping ingestion, validation, watermark check, delta application, version creation, and audit logging into a single atomic transaction boundary with exponential backoff and session expunging. | [`backend/app/pipeline.py`](file:///c:/Users/nisham/Desktop/UNIVERSITY_DATA/backend/app/pipeline.py)<br>[`backend/tests/test_failure_injection.py`](file:///c:/Users/nisham/Desktop/UNIVERSITY_DATA/backend/tests/test_failure_injection.py) |
| **4. "Delta recalculation performed $O(N)$ table scans, creating scalability bottlenecks."** | Ingesting a late event triggered full-table recalculation and JSON deserialization of all past events for that date. | Refactored engine to $O(1)$ stateful delta math: incremental contribution $\delta$ is extracted directly from the payload and added to current aggregate. Ground truth computation is reserved for reconciliation validation and manual approvals. | Latency reduced to 21–38ms for 5000 events |
| **5. "Frontend lacked version lineage visualization and human review context."** | Review UI displayed simple approve buttons without explanation; reports did not show version histories. | Built interactive Version Lineage Timeline ($v1 \to v2 \to v3$), Before/After diff cards, "Why is this flagged?" explanation panels, and action confirmation modals in the React frontend. Added Engine Diagnostics tab. | [`frontend/src/components/ReportsTab.jsx`](file:///c:/Users/nisham/Desktop/UNIVERSITY_DATA/frontend/src/components/ReportsTab.jsx)<br>[`frontend/src/components/ReviewTab.jsx`](file:///c:/Users/nisham/Desktop/UNIVERSITY_DATA/frontend/src/components/ReviewTab.jsx) |

---

## 3. Mathematical Reconciliation & Invariant Verification

The system enforces the strict institutional correctness invariant:
$$\text{CorrectedAggregate}(D) \equiv \text{GroundTruth}(D) \quad \forall D \in \text{Reporting Dates}$$

### Experimental Validation Across 6 Stress Scenarios (Seed = 42)

The experimental suite was executed against the hardened WAL database engine across 6 representative institutional scenarios (200 events each, total 1,200 events):

| Scenario ID & Stress Profile | Late Ratio | Duplicates | Invalid | Baseline MAE | Corrected MAE | Baseline RMSE | Corrected RMSE | Exact Match % |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Scenario 1: 0% Late Events (Ideal Baseline)** | 0.0% | 0 | 0 | 53.37 | **0.000** | 93.50 | **0.000** | **100.0%** |
| **Scenario 2: 5% Late Events (Mild Delay)** | 5.0% | 2 | 0 | 55.36 | **0.000** | 101.67 | **0.000** | **100.0%** |
| **Scenario 3: 10% Late Events (Standard Stream)** | 10.0% | 4 | 2 | 58.42 | **0.000** | 119.67 | **0.000** | **100.0%** |
| **Scenario 4: 25% Late Events (Network Outage)** | 25.0% | 6 | 4 | 100.04 | **0.000** | 213.72 | **0.000** | **100.0%** |
| **Scenario 5: Duplicate-Heavy Stream (Retries)** | 15.0% | 30 | 4 | 70.48 | **0.000** | 130.46 | **0.000** | **100.0%** |
| **Scenario 6: Very Late Events (Multi-Day Lag)** | 30.0% | 10 | 10 | 117.25 | **0.000** | 222.37 | **0.000** | **100.0%** |

**Observation:** While baseline uncorrected daily reports suffer dramatic error escalation (MAE rising from $53.37$ to $117.25$ and RMSE rising from $93.50$ to $222.37$), the stateful delta engine achieves **$0.000$ error and 100.0% exact match** across all scenarios.

---

## 4. Performance & Scalability Summary

As documented in [`docs/PERFORMANCE_REPORT.md`](file:///c:/Users/nisham/Desktop/UNIVERSITY_DATA/docs/PERFORMANCE_REPORT.md), the system underwent empirical benchmarking up to 5,000 events:
- **Throughput:** Sustained single-worker throughput of **43.51 to 47.28 events/sec** during sequential scaling; peaking at **163.63 events/sec** during replay streams.
- **Latency:** Average ingestion and recalculation latency under **38.6 ms** across all workloads; P95 under **70.8 ms**.
- **Memory Footprint:** Peak RAM consumption strictly between **0.44 MB and 0.98 MB**, demonstrating that the system does not introduce memory leaks or unbounded buffer growth.
- **Commodity Hardware Viability:** Fully deployable on institutional low-cost edge micro-servers (dual-core, 4GB RAM) without requiring specialized distributed cluster hardware.

---

## 5. Software Quality & Testing Assurance

The codebase maintains a 100% automated test pass rate across 23 comprehensive tests:
```
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.1.1, pluggy-1.6.0
collected 23 items

backend/tests/test_audit_rollback.py ..                                  [  8%]
backend/tests/test_concurrency.py .....                                  [ 30%]
backend/tests/test_correction.py ...                                     [ 43%]
backend/tests/test_database_hardening.py .....                           [ 65%]
backend/tests/test_failure_injection.py ..                               [ 73%]
backend/tests/test_integration.py .                                      [ 78%]
backend/tests/test_pipeline.py ....                                      [ 95%]
backend/tests/test_reconciliation.py .                                   [100%]

============================= 23 passed in 8.28s ==============================
```

Frontend production bundle verification via Vite:
- `✓ 2313 modules transformed`
- `✓ built in 26.35s with 0 errors`

---

## 6. Project Roadmap: Final 30% Implementation Plan (Towards 100% Viva)

To achieve 100% completion for final institutional review and defense, the following milestones are scheduled:

1. **Distributed Storage Backend (Phase 8 - Oct 2026):** Provide a dual-driver database configuration enabling zero-downtime migration from local SQLite WAL to PostgreSQL + TimescaleDB for multi-campus deployment.
2. **Streaming Ingestion Connectors (Phase 9 - Nov 2026):** Implement asynchronous event consumption via Apache Kafka / Redis Streams to decouple HTTP gateway ingress from database writing.
3. **Role-Based Access Control & Institutional SSO (Phase 10 - Dec 2026):** Integrate OAuth2 / JWT authentication with role hierarchy (Dean, Department Head, Faculty Coordinator, Auditor).
4. **Automated Anomaly Detection (Phase 11 - Jan 2027):** Train isolation forest models to flag sudden bulk late-event injections (e.g., student attendance manipulation or exam score tampering).
5. **Final Dissertation & Viva Presentation (Feb 2027):** Comprehensive final academic thesis, viva defense slides, and institutional deployment handbook.
