# Pre-Final Baseline Verification Report
**Project:** Late-Event Correction & Daily Reporting System  
**Institution:** Rathinam Technical Campus (Autonomous), Coimbatore  
**Milestone:** Baseline Prior to Final 30% Hardening  
**Verification Date:** September 29, 2026  
**Auditor:** Antigravity Senior Engineering Pair  

---

## 1. Overview & Verification Protocol

Before introducing any modifications for the final 30% milestone, the existing codebase was completely audited and executed locally without modifications. All results in this report represent **actual measured system outputs** from live executions in the local workspace environment.

No values have been simulated, assumed, or fabricated.

---

## 2. Automated Test Suite Baseline

The full backend automated test suite was executed using `pytest` in the project's Python virtual environment (`.\venv\Scripts\python -m pytest backend/tests`).

### Execution Summary
| Metric | Measured Value |
|---|---|
| **Total Test Files** | 8 files |
| **Total Tests Collected** | 23 items |
| **Tests Passed** | **23 passed** |
| **Tests Failed** | **0 failed** |
| **Tests Skipped** | **0 skipped** |
| **Execution Duration** | **150.26 seconds (2m 30s)** |
| **Platform** | Windows 11 (win32), Python 3.14.3, pytest-9.1.1, pluggy-1.6.0 |

### Detailed Test Execution Breakdown
| Test Suite File | Test Count | Result | Key Verified Assertions |
|---|---|---|---|
| `backend/tests/test_audit_rollback.py` | 2 | PASSED | Compensating rollback execution, monotonic report version increment, audit trail generation |
| `backend/tests/test_concurrency.py` | 5 | PASSED | Test A (Duplicate race), Test B (Concurrent unique events), Test C (Concurrent late events), Test D (Review approval conflict protection), Test E (Rollback idempotency) |
| `backend/tests/test_correction.py` | 3 | PASSED | High-impact threshold drift evaluation (≥15%), automated correction for low-impact drift (<15%), forced review on academic outcome alterations |
| `backend/tests/test_database_hardening.py` | 5 | PASSED | SQLite WAL mode & foreign keys enabled via PRAGMA, `DailyReport` composite uniqueness (`reporting_date`, `domain`), `ReportVersion` uniqueness (`report_id`, `version_number`), 24h lateness boundary, 15% drift boundary |
| `backend/tests/test_failure_injection.py` | 2 | PASSED | Staged atomic rollback on I/O error (no orphaned `RawEvent`), clean rollback on `ReportVersion` creation failure |
| `backend/tests/test_integration.py` | 1 | PASSED | End-to-end event lifecycle: Ingestion -> Lateness Detection -> Delta Recalculation -> Review Queue -> Approval -> Version Lineage |
| `backend/tests/test_pipeline.py` | 4 | PASSED | Idempotent event ingestion, domain payload schema validation across 4 domains, duplicate discard with zero aggregate contribution |
| `backend/tests/test_reconciliation.py` | 1 | PASSED | Multi-day reconciliation invariant: $CorrectedAggregate(D) \equiv GroundTruth(D)$ across 300 synthetic events with 25% late ratio |

---

## 3. Frontend Production Build Baseline

The frontend application (`frontend/`) was built using Vite and TailwindCSS via `npm run build`.

### Build Summary
```text
> rtc-late-event-reporting-system@1.0.0 build
> vite build

vite v5.4.21 building for production...
transforming...
✓ 2313 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.80 kB │ gzip:   0.48 kB
dist/assets/index-DEouaQ3Z.css   26.07 kB │ gzip:   5.25 kB
dist/assets/index-DrWqoXYO.js   591.32 kB │ gzip: 164.26 kB
✓ built in 2m 43s
```
- **Build Outcome:** Succeeded with zero compile errors.
- **HTML Bundle:** `dist/index.html` (0.80 kB)
- **CSS Bundle:** `dist/assets/index-DEouaQ3Z.css` (26.07 kB)
- **JavaScript Bundle:** `dist/assets/index-DrWqoXYO.js` (591.32 kB)

---

## 4. Database Engine Baseline Configuration

The SQLite database configuration was verified via runtime PRAGMA inspection:

| Setting | Value | Implementation Mechanism | Purpose |
|---|---|---|---|
| **Engine** | SQLite 3 | SQLAlchemy `create_engine` | Embedded relational database |
| **Journal Mode** | `WAL` (Write-Ahead Logging) | `PRAGMA journal_mode=WAL;` | Concurrent non-blocking reads during active transactions |
| **Busy Timeout** | `10000` ms (10 seconds) | `PRAGMA busy_timeout=10000;` | Prevents `sqlite3.OperationalError: database is locked` under concurrency |
| **Foreign Keys** | `1` (Enabled) | `PRAGMA foreign_keys=ON;` | Enforces referential integrity across students, events, reports, and versions |
| **Synchronous Mode** | `NORMAL` | `PRAGMA synchronous=NORMAL;` | Optimal balance of ACID durability and high write throughput for WAL |
| **Connection Timeout** | `15` seconds | `connect_args={"timeout": 15}` | Driver-level timeout for connection acquisition |
| **Pool Pre-Ping** | `True` | SQLAlchemy engine argument | Detects dead or disconnected connection handles |

---

## 5. Performance Benchmark Baseline

The performance benchmark suite (`data/results/performance_benchmark.json`) yielded the following verified baseline metrics across scaling event volumes:

### Event Scaling Performance
| Event Count | Duration (s) | Throughput (eps) | Avg Latency (ms) | Median Latency (ms) | P95 Latency (ms) | P99 Latency (ms) | Peak RAM (MB) | Database Size | Ground Truth Match |
|---|---|---|---|---|---|---|---|---|---|
| **100** | 2.30s | 43.51 | 22.98ms | 21.80ms | 36.88ms | 137.14ms | 0.98 MB | 380 KB | 100.0% |
| **500** | 10.58s | 47.28 | 21.14ms | 20.50ms | 33.66ms | 46.44ms | 0.44 MB | 1,356 KB | 100.0% |
| **1,000** | 21.79s | 45.90 | 21.78ms | 20.64ms | 37.26ms | 52.97ms | 0.45 MB | 2,552 KB | 100.0% |
| **5,000** | 192.85s | 25.93 | 38.56ms | 32.77ms | 70.80ms | 116.05ms | 0.57 MB | 11,644 KB | 100.0% |

### Historical Replay Workload Baseline (4,000 Events)
| Workload Profile | Events Replayed | Duration (s) | Throughput (eps) | Avg Latency (ms) | P95 Latency (ms) | Peak Memory |
|---|---|---|---|---|---|---|
| **Normal Institutional Stream** | 1,000 | 31.53s | 31.72 | 31.52ms | 53.12ms | 0.42 MB |
| **Late-Event-Heavy Stream** | 1,000 | 7.50s | 133.33 | 7.49ms | 11.73ms | 0.07 MB |
| **Duplicate-Heavy Stream** | 1,000 | 6.11s | 163.63 | 6.10ms | 7.96ms | 0.06 MB |
| **7-Day Delayed Ingestion Lag** | 1,000 | 6.51s | 153.66 | 6.50ms | 9.22ms | 0.07 MB |
| **Total Replay Summary** | **4,000** | **51.65s** | **77.45 eps** | — | — | **0.42 MB** |

---

## 6. Six Experimental Stress Scenarios Baseline

The mathematical experiment suite (`data/results/experiment_summary.json`) verifies ground-truth convergence across 6 stress scenarios:

| Scenario | Late Ratio | Total Events | Baseline MAE | Corrected MAE | Exact Match % | Processing Time |
|---|---|---|---|---|---|---|
| **1. 0% Late Events** | 0% | 200 | 53.37 | **0.00** | **100.0%** | 2,222.8 ms |
| **2. 5% Late Events** | 5% | 200 | 55.36 | **0.00** | **100.0%** | 2,362.6 ms |
| **3. 10% Late Events** | 10% | 200 | 58.42 | **0.00** | **100.0%** | 2,313.1 ms |
| **4. 25% Late Events** | 25% | 200 | 100.04 | **0.00** | **100.0%** | 2,321.0 ms |
| **5. Duplicate Events** | 15% | 200 | 70.48 | **0.00** | **100.0%** | 2,228.1 ms |
| **6. Very Late Events** | 30% | 200 | 117.25 | **0.00** | **100.0%** | 2,561.5 ms |

---

## 7. Baseline Conclusion

The baseline system is operational, resilient, and mathematically sound. The final 30% milestone will directly address the evaluator's three primary demands by:
1. Hardening API schemas and error responses (introducing explicit Pydantic response models, HTTP 409 Conflict handling, and standardized error boundaries).
2. Providing a standalone benchmark CLI (`scripts/run_performance_benchmark.py`) with rich environment diagnostics, min/max latencies, and free-tier viability documentation.
3. Enhancing Human-in-the-Loop review UX with dynamic textual explanations, rejection reason logging, report version timelines, audit lineage filters, and comprehensive screenshot evidence.
