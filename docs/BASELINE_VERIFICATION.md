# Baseline Verification Report (35% Baseline)

**Project Title:** Late-Event Correction & Daily Reporting System  
**Institution:** Rathinam Technical Campus (Autonomous), Coimbatore  
**Verification Date:** September 28, 2026  
**Environment:** Python 3.14.3, pytest 9.1.1, Node v22.18.0 / Vite 5.4.21, SQLite 3  

---

## 1. Automated Test Suite Baseline

The automated test suite was executed against the existing repository code prior to making architectural modifications:

```bash
.\venv\Scripts\python -m pytest backend/tests
```

### Result:
- **Total Test Cases:** 11
- **Passed:** 11
- **Failed:** 0
- **Execution Time:** 7.43 seconds
- **Pass Rate:** 100%

### Breakdown of Verified Test Modules:
1. `backend/tests/test_audit_rollback.py`:
   - `test_rollback_compensating_action`: PASSED (reverts aggregate, increments report version, logs audit entry)
   - `test_rollback_idempotency_guard`: PASSED (subsequent rollback on same correction returns `ALREADY_ROLLED_BACK`)
2. `backend/tests/test_correction.py`:
   - `test_on_time_correction_and_ground_truth`: PASSED (on-time aggregation yields zero error against ground truth)
   - `test_late_event_recalculation`: PASSED (late event arriving 3 days later increments version and corrects historical aggregate)
   - `test_high_impact_forced_review`: PASSED (placement offer change isolates into `PENDING_REVIEW` queue until approved)
3. `backend/tests/test_integration.py`:
   - `test_full_end_to_end_integration_flow`: PASSED (150 synthetic events across 4 domains with late, duplicate, and invalid events; all reports converge to ground truth)
4. `backend/tests/test_pipeline.py`:
   - `test_on_time_event_ingestion`: PASSED (delay <= 24h classified as `is_late=False`)
   - `test_late_event_ingestion`: PASSED (delay > 24h classified as `is_late=True`)
   - `test_idempotency_duplicate_discard`: PASSED (duplicate event ID discarded with 0 contribution to aggregate)
   - `test_invalid_payload_handling`: PASSED (malformed payload flagged as `INVALID`)
5. `backend/tests/test_reconciliation.py`:
   - `test_final_corrected_aggregate_equals_ground_truth`: PASSED (300 events across multiple dates; zero mismatches between corrected state and ground truth)

---

## 2. Frontend Build Verification

The frontend production build was verified using Vite:

```bash
npm run build
```

### Result:
- **Build Status:** SUCCESS (Exit Code 0)
- **Modules Transformed:** 2,312 modules
- **Output Artifacts:**
  - `dist/index.html`: 0.80 kB
  - `dist/assets/index-*.css`: 24.18 kB
  - `dist/assets/index-*.js`: 571.41 kB
- **Lint / Syntax Errors:** 0

---

## 3. Existing Experimental Results Baseline

The existing recorded 6 stress scenarios (`data/results/experiment_summary.json`) confirm the system's baseline thesis:

| Scenario | Late Ratio | Total Events | Baseline MAE | Corrected MAE | Exact Match % | Processing Time (ms) |
|---|---|---|---|---|---|---|
| **Scenario 1: 0% Late Events** | 0.0% | 200 | 53.36 | **0.0000** | 100.0% | 2,202.41 |
| **Scenario 2: 5% Late Events** | 5.0% | 200 | 55.36 | **0.0000** | 100.0% | 1,922.36 |
| **Scenario 3: 10% Late Events** | 10.0% | 200 | 58.42 | **0.0000** | 100.0% | 1,956.08 |
| **Scenario 4: 25% Late Events** | 25.0% | 200 | 100.04 | **0.0000** | 100.0% | 1,798.75 |
| **Scenario 5: Duplicate Events** | 15.0% | 200 | 70.48 | **0.0000** | 100.0% | 1,634.28 |
| **Scenario 6: Very Late Events** | 30.0% | 200 | 117.25 | **0.0000** | 100.0% | 1,886.31 |

**Observation:** While the naive baseline error deteriorates rapidly as late events increase from 0% to 30% (MAE rises from 53.36 to 117.25), the late-event correction engine achieves **Corrected MAE = 0.0000** with **100% exact match** across all scenarios.

---

## 4. Key Gaps to Address for 70% Review

1. **Database Schema:** Missing composite unique constraints on `DailyReport(reporting_date, domain)` and `ReportVersion(report_id, version_number)`.
2. **SQLite WAL & Concurrency:** Database currently uses default journal mode; SQLite connection lacks WAL pragmas, busy timeouts, and connection-level foreign keys.
3. **Transaction Safety:** Separate commits in ingestion and correction steps risk inconsistent state if an unhandled failure occurs during correction or versioning.
4. **Concurrency Tests:** Zero automated multi-threaded tests to prove race condition safety.
5. **Real-time Performance Metrics:** Latency (p95, p99), throughput (eps), and memory profiles must be measured and surfaced via both API and UI.
6. **Human-in-the-Loop Explainability:** Pending review cards need explicit reasoning ("Why was this escalated?"), visual before/after aggregate diffs, and modal confirmations.
