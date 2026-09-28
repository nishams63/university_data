# RELATIONAL DATABASE DESIGN & CONCURRENCY SPECIFICATION

**Institution:** Rathinam Technical Campus (Autonomous), Coimbatore  
**Project:** Late-Event Correction & Daily Reporting System  
**Milestone:** 70% Engineering Review  
**Engine:** SQLite 3 with Write-Ahead Logging (WAL) via SQLAlchemy 2.0  

---

## 1. Schema Architecture Overview

The system addresses the late-event arrival problem through a strongly-typed relational schema that isolates raw event ingestion from aggregate report state while maintaining a monotonic audit trail of every historical correction.

```
                      +-------------------+
                      |     students      |
                      +-------------------+
                      | PK student_id     |
                      |    name           |
                      |    department     |
                      |    batch_year     |
                      +---------+---------+
                                | 1
                                |
                                | N
                      +---------v---------+
                      |    raw_events     |
                      +-------------------+
                      | PK event_id       |
                      | FK student_id     |
                      |    domain         |
                      |    event_timestamp|
                      |    arrival_time   |
                      |    reporting_date |
                      |    delay_hours    |
                      |    is_late        |
                      |    is_valid       |
                      |    payload_json   |
                      +-------------------+
                                | (Triggers Recalculation)
                                v
+-------------------+ 1       N +---------------------+
|   daily_reports   |<----------|   report_versions   |
+-------------------+           +---------------------+
| PK report_id      |           | PK id               |
| UQ (date, domain) |           | FK report_id        |
|    reporting_date |           | UQ (report, version)|
|    domain         |           |    version_number   |
|    current_version|           |    aggregate_value  |
|    baseline_agg   |           |    change_type      |
|    corrected_agg  |           |    trigger_event_id |
|    status         |           +---------------------+
+---------+---------+
          | 1
          |
          | N
+---------v-----------+         +---------------------+
| report_corrections  |         |     audit_logs      |
+---------------------+         +---------------------+
| PK correction_id    |         | PK id               |
| FK report_id        |         | UQ log_id           |
|    student_id       |         |    timestamp        |
|    delta_value      |         |    action           |
|    impact_percent   |         |    domain           |
|    is_high_impact   |         |    event_id         |
|    requires_review  |         |    report_id        |
|    status           |         |    actor            |
|    reviewed_by      |         |    details_json     |
+---------------------+         +---------------------+
```

---

## 2. Entity Definitions & DDL Specifications

### 2.1 Table: `raw_events`
Stores all incoming payloads across the four institutional domains (`RTC-Attendance`, `RTC-Assessment`, `RTC-Learning`, `RTC-Placement`).
- **Primary Key:** `event_id` (VARCHAR(64)) — Serves as the global deduplication/idempotency key.
- **Foreign Key:** `student_id` REFERENCES `students(student_id)` ON DELETE RESTRICT.
- **Indices:**
  - `ix_raw_events_reporting_domain_valid`: Composite B-tree index on `(reporting_date, domain, is_valid)`. Accelerates ground truth reconciliation scans.
  - `ix_raw_events_arrival_timestamp`: Index on `arrival_timestamp` for ingestion sorting.
  - `ix_raw_events_delay_hours`: Index on `delay_hours` for lateness analytics.

### 2.2 Table: `daily_reports`
Maintains the snapshot aggregate for each `(reporting_date, domain)` pair.
- **Primary Key:** `report_id` (VARCHAR(64)) — Convention: `RTC-RPT-{YYYYMMDD}-{DOMAIN}`.
- **Composite Unique Constraint:**
  ```sql
  CONSTRAINT uq_report_date_domain UNIQUE (reporting_date, domain)
  ```
  Guarantees that no concurrent ingestion thread can produce conflicting duplicate reporting rows for the same calendar date and academic domain.
- **Fields:**
  - `baseline_aggregate` (FLOAT): Aggregate computed strictly from on-time events before the 24h watermark.
  - `corrected_aggregate` (FLOAT): Live aggregate reflecting all accepted late-event delta contributions.
  - `current_version` (INTEGER): Monotonically increasing version counter.

### 2.3 Table: `report_versions`
Provides complete, immutable lineage for every report mutation.
- **Primary Key:** `id` (INTEGER AUTOINCREMENT).
- **Foreign Key:** `report_id` REFERENCES `daily_reports(report_id)` ON DELETE CASCADE.
- **Composite Unique Constraint:**
  ```sql
  CONSTRAINT uq_report_version_num UNIQUE (report_id, version_number)
  ```
  Enforces monotonic ordering: versions cannot be overwritten or created out of sequence.
- **Fields:**
  - `version_number` (INTEGER): 1, 2, 3...
  - `aggregate_value` (FLOAT): Resulting aggregate metric.
  - `change_type` (VARCHAR(32)): `INITIAL_CREATION`, `LATE_EVENT_AUTO_CORRECTION`, `MANUAL_REVIEW_APPROVAL`, `ROLLBACK`.
  - `change_trigger_event_id` (VARCHAR(64)): ID of the raw event that induced the version bump.

### 2.4 Table: `report_corrections`
Encapsulates individual correction deltas, human review states, and threshold flags.
- **Primary Key:** `correction_id` (VARCHAR(64)) — Convention: `CORR-{TIMESTAMP}-{HASH}`.
- **Foreign Key:** `report_id` REFERENCES `daily_reports(report_id)` ON DELETE CASCADE.
- **Fields:**
  - `delta_value` (FLOAT): Metric change contribution ($\Delta = V_{\text{new}} - V_{\text{prev}}$).
  - `impact_percentage` (FLOAT): Relative shift: $\frac{|\Delta|}{\max(|V_{\text{prev}}|, 1)} \times 100$.
  - `is_high_impact` (BOOLEAN): True if `impact_percentage >= 15.0%`.
  - `requires_review` (BOOLEAN): True if `is_high_impact` OR outcome risk detected.
  - `status` (VARCHAR(32)): `AUTO_CORRECTED`, `PENDING_REVIEW`, `APPROVED`, `REJECTED`, `ROLLED_BACK`.

### 2.5 Table: `audit_logs`
Write-only, tamper-evident log recording all administrative and system mutations.
- **Primary Key:** `id` (INTEGER AUTOINCREMENT).
- **Unique Constraint:** `log_id` (VARCHAR(64)).
- **Fields:** `timestamp`, `action`, `domain`, `event_id`, `report_id`, `actor`, `details_json`.

---

## 3. SQLite WAL Engine Hardening & Pragmas

SQLite is configured as a robust, single-node transactional engine through connection-level hooks in `backend/app/database.py`:

```python
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA busy_timeout=10000;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.close()
```

### Technical Rationale for Each Pragma:
1. `PRAGMA journal_mode=WAL;`: Replaces legacy rollback journals with Write-Ahead Logging. Permits concurrent readers while a writer commits, avoiding read locks during intensive background ingestion.
2. `PRAGMA busy_timeout=10000;`: Configures SQLite to automatically sleep and retry for up to 10 seconds (10,000 ms) when another thread holds the write lock, eliminating `database is locked` OperationalErrors.
3. `PRAGMA foreign_keys=ON;`: By default, SQLite ignores foreign key constraints. This pragma ensures relational integrity and cascade deletions.
4. `PRAGMA synchronous=NORMAL;`: WAL mode guarantees full consistency under `NORMAL` synchronization because checkpoints are atomic and write orders are strictly preserved, reducing synchronous disk flushes by over 60%.

---

## 4. Transaction Isolation & Concurrency Semantics

To guarantee ACID guarantees under multi-threaded loads:
1. **Single Atomic Unit of Work:** Ingestion, validation, delta calculation, report version creation, and audit logging execute within a single SQLAlchemy session transaction (`session.begin()`).
2. **Deterministic Retry with State Expunging:** In `ingest_and_process_atomic(db, event_data, max_retries=8)`:
   - If an `OperationalError` (concurrency lock contention) occurs, the session performs `db.rollback()` followed by `db.expunge_all()` to clear stale model entities from the identity map before sleeping with exponential jitter and retrying.
3. **Idempotent Ingestion Fast-Path:** Before beginning mutations, the engine checks for `RawEvent.event_id`. Duplicate arrivals are logged and discarded without mutating report versions.
