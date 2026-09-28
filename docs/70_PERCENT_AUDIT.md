# System Audit: 35% Baseline to 70% Engineering Prototype

**Project Title:** Late-Event Correction & Daily Reporting System: A Stateful Watermark and Delta Recalculation Engine for Institutional Big Data  
**Institution:** Rathinam Technical Campus (Autonomous), Coimbatore  
**Target Milestone:** 70% Milestone Implementation Review  
**Audit Date:** September 2026  
**Auditor:** Senior Engineering Team (Distributed Systems, Data Engineering, QA)

---

## 1. Executive Summary

This comprehensive audit inspects the existing repository baseline (~35% academic proof-of-concept) against the feedback from the previous project evaluation and the technical requirements for the 70% milestone. 

The core thesis of the system is valid: traditional institutional reporting engines bind incoming records to their ingestion date or freeze historical reports, producing significant metric distortion when events arrive late (e.g., delayed biometric attendance, medical leaves, late quiz synchronizations, placement offer letters). This system implements event-time windowing, dynamic delta recalculation, impact-driven human review queues, report versioning, and ground-truth reconciliation.

However, the previous 35% implementation suffered from several critical engineering weaknesses:
1. **Database Schema Constraints:** Missing database-level uniqueness on composite keys (e.g., `(reporting_date, domain)` on `DailyReport`, `(report_id, version_number)` on `ReportVersion`), relying partially on application-level checks.
2. **SQLite Concurrency & WAL:** SQLite was initialized in default rollback journal mode without Write-Ahead Logging (WAL), busy timeout configuration, or foreign key enforcement pragmas.
3. **Transaction Boundaries:** Ingestion and correction were separate steps with intermediate commits, risking partial state persistence if failure occurred midway.
4. **Concurrency Safety:** Zero automated concurrency tests existed; concurrent ingestion of identical or conflicting events was unverified under real multi-threaded execution.
5. **Benchmarking & Profiling:** No automated latency, throughput (eps), or memory measurement engine existed.
6. **Human-in-the-Loop Review UX:** Review interface lacked rich contextual explanation of why a change was flagged, visual before/after diffs, and modal confirmations.
7. **Watermark Observability:** Watermark concept was represented solely as a static 24-hour threshold without real-time tracking of observed event time vs. processing time.

---

## 2. Component-by-Component Audit Matrix

| Feature / Component | Expected Behavior (70% Target) | Current Implementation (35% Baseline) | Status | Relevant File(s) | Required Remediation |
|---|---|---|---|---|---|
| **Database Engine & Connection** | SQLite WAL mode, `busy_timeout=10000`, `foreign_keys=ON`, `synchronous=NORMAL`, thread-safe pool | Default SQLite connection, no PRAGMA hooks, `check_same_thread=False` | **Partial** | `backend/app/database.py` | Add SQLAlchemy event listener `connect` to set PRAGMA `journal_mode=WAL`, `busy_timeout=10000`, `foreign_keys=ON`. |
| **RawEvent Schema** | Primary key `event_id`, foreign key to `students.student_id`, unique constraint, index on timestamps and domain | Has `event_id` PK, `ForeignKey("students.student_id")`, `uq_event_id` constraint | **Working** | `backend/app/models.py` | Verify foreign key enforcement via SQLite PRAGMA; add indices if missing. |
| **DailyReport Schema** | `UNIQUE(reporting_date, domain)` constraint to prevent duplicate report rows during concurrent writes | Only `report_id` unique constraint; no composite unique on `(reporting_date, domain)` | **Partial** | `backend/app/models.py` | Add `UniqueConstraint('reporting_date', 'domain', name='uq_daily_report_date_domain')`. |
| **ReportVersion Schema** | Monotonic versions; `UNIQUE(report_id, version_number)` to prevent duplicate version records | No unique constraint on `(report_id, version_number)` | **Partial** | `backend/app/models.py` | Add `UniqueConstraint('report_id', 'version_number', name='uq_report_version_num')`. |
| **ReportCorrection Schema** | Track correction lineage, previous/new values, impact %, status, review metadata | Implemented with status lifecycle (`AUTO_CORRECTED`, `PENDING_REVIEW`, `APPROVED`, etc.) | **Working** | `backend/app/models.py`, `backend/app/correction.py` | Add index on `(report_id, status)` and link to trigger `event_id`. |
| **AuditLog Immutability** | Append-only audit records; no update/delete APIs; structured JSON payload | Implemented with auto-generated IDs and JSON payloads | **Working** | `backend/app/models.py`, `backend/app/audit.py` | Enforce read-only access in API; prevent update/delete routes. |
| **Atomic Ingestion & Correction** | Ingestion + Delta recalculation + Report Update + Versioning + Audit within single atomic transaction | `ingest_raw_event` commits raw event, then `process_and_apply_corrections` commits report updates separately | **Broken** | `backend/app/pipeline.py`, `backend/app/correction.py` | Create atomic orchestration function `ingest_and_process_atomic()` with unified commit/rollback. |
| **Duplicate Event Race Handling** | Multi-threaded duplicate submissions handled deterministically; exactly one event committed | Application query check followed by catch of `IntegrityError` | **Partial** | `backend/app/pipeline.py` | Validate and stress-test under concurrent threads in `test_concurrency.py`. |
| **Late-Event Classification** | Event timestamp vs. Arrival timestamp > 24 hours categorized as `is_late=True` | Implemented and configurable via `LATE_THRESHOLD_HOURS` | **Working** | `backend/app/pipeline.py`, `backend/app/config.py` | Add boundary tests (exactly 24.0h vs 24.01h). |
| **High-Impact Threshold & Review Queue** | Drift >= 15% AND abs(delta) >= 5.0 OR forced high-risk status -> `PENDING_REVIEW` | Implemented in `correction.py` with 15% threshold and placement status triggers | **Working** | `backend/app/correction.py` | Add edge cases tests (14.99% vs 15.00%). |
| **Compensating Rollback** | Idempotent compensating rollback appending a new report version | Implemented in `audit.py` with `ALREADY_ROLLED_BACK` guard | **Working** | `backend/app/audit.py` | Add concurrent rollback race test. |
| **Ground-Truth Reconciliation** | Incremental calculation matches independent ground-truth recalculation | Tested in `test_reconciliation.py`; 100% exact match verified | **Working** | `backend/app/correction.py`, `backend/tests/test_reconciliation.py` | Verify independence of ground-truth calculation method. |
| **Concurrency Testing** | Multi-threaded tests for duplicate race, concurrent unique writes, concurrent late events, review race | Completely missing | **Missing** | `backend/tests/test_concurrency.py` | Implement comprehensive test suite using `concurrent.futures`. |
| **Failure Injection Testing** | Controlled exceptions during ingestion/correction to verify transaction rollback | Completely missing | **Missing** | `backend/tests/test_failure_injection.py` | Implement tests verifying rollback upon forced failures. |
| **Performance Benchmarking** | Measure throughput (eps), latency (avg, p95, p99), peak memory, historical replay | Static demo script only; no formal benchmarking suite | **Missing** | `backend/app/benchmarks.py`, `scripts/run_benchmarks.py` | Build benchmark framework measuring real execution parameters on 100 to 5000+ events. |
| **API Contract & Status Codes** | Explicit Pydantic response models, REST status codes (201, 200, 400, 404, 409, 422) | Returns dicts in some endpoints; Pydantic deprecation warnings | **Partial** | `backend/app/main.py`, `backend/app/schemas.py` | Upgrade schemas to Pydantic V2 `ConfigDict`; add explicit models and status codes. |
| **System Health & Watermark API** | Expose DB connection, WAL status, foreign keys, pending reviews, watermark stats | Basic `/api/health` returning static strings | **Partial** | `backend/app/main.py` | Enhance `/api/health` with live DB diagnostics; add `/api/watermark`. |
| **Human-in-the-Loop Review UI** | Explanation panel ("Why is this flagged?"), Before/After diff, modal confirmations | Basic cards with simple approve/reject alert confirm | **Partial** | `frontend/src/components/ReviewTab.jsx` | Add explanation generator, visual Before/After diff cards, modal dialogs. |
| **Report Version History UI** | Timeline of version lineage (v1 -> v2 -> v3) with trigger event, actor, delta | Reports table exists, but version timeline modal is basic | **Partial** | `frontend/src/components/ReportsTab.jsx` | Implement rich interactive version history drawer/modal. |
| **Audit Explorer UI** | Filterable by domain, action, date, event ID; structured detail viewer | Basic table without multi-attribute filtering | **Partial** | `frontend/src/components/AuditTab.jsx` | Add domain, action, and text search filters. |
| **Performance & Metrics Dashboard** | Visual dashboard displaying throughput, latencies, memory, replay statistics | Only standard high-level counts in `DashboardTab` | **Partial** | `frontend/src/components/DashboardTab.jsx` | Add Performance & Health sections displaying real benchmark metrics. |
| **Experimental Scenarios** | 6 stress scenarios (0%, 5%, 10%, 25%, duplicates, 30% late) | Implemented in `experiments.py`; outputs in `experiment_summary.json` | **Working** | `backend/app/experiments.py` | Re-run and verify reproducibility with seed 42. |

---

## 3. Prioritized Action Plan for 70% Milestone

1. **Database Hardening:** Configure SQLite WAL, foreign key pragmas, busy timeouts, and add unique constraints to `DailyReport` and `ReportVersion`.
2. **Transaction Atomicity:** Refactor ingestion + delta recalculation into a single atomic transaction boundary.
3. **Concurrency Test Suite:** Implement `backend/tests/test_concurrency.py` verifying race-condition resilience across all critical flows.
4. **Failure Injection Suite:** Implement `backend/tests/test_failure_injection.py` to confirm zero state corruption on unexpected exceptions.
5. **Performance Benchmark Engine:** Build `backend/app/benchmarks.py` and `scripts/run_benchmarks.py` to collect real latency, throughput, and memory metrics.
6. **API Hardening:** Modernize `schemas.py` with Pydantic v2 `ConfigDict`, add `/api/metrics/performance`, `/api/watermark`, and comprehensive `/api/health`.
7. **Frontend Enhancements:** Upgrade ReviewTab with rich explanations, Before/After diffs, Report Version Timeline, Audit Filtering, and Performance Visualization.
8. **Documentation & Validation:** Produce all required architectural, database, performance, and project reports based solely on actual measured execution.
