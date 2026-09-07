# Architecture Specification — RATHINAM TECHNICAL CAMPUS

## 1. Overview & System Objectives

The **Rathinam Technical Campus Late-Event Correction & Reporting System** provides robust data quality management for institutional reporting across four domains: `RTC-Learning`, `RTC-Assessment`, `RTC-Attendance`, and `RTC-Placement`.

The architecture enforces strict separation between event ingestion, stateful delta recalculation, ground truth calculation, review workflow management, and presentation layers.

---

## 2. Timestamp Semantics

To prevent temporal distortion, the system enforces four distinct timestamp attributes:

1. `event_timestamp`: The ISO timestamp indicating when the physical university activity occurred (e.g. lecture attendance at 2026-08-20 09:00:00). Reporting date $D$ is strictly derived as `event_timestamp.date()`.
2. `arrival_timestamp`: The ISO timestamp when the event reached the central RTC ingestion system.
3. `processing_timestamp`: The ISO timestamp when the correction engine evaluated the event.
4. `batch_id`: The batch identifier associated with the ingestion payload.

### Lateness Rule
Lateness is dynamically classified via configurable threshold:
$$\text{delay\_hours} = \frac{\text{arrival\_timestamp} - \text{event\_timestamp}}{3600}$$
If $\text{delay\_hours} > \text{LATE\_THRESHOLD\_HOURS}$ (default: 24.0 hours), the event is tagged as `LATE`.

---

## 3. Database Schema & Models

The system uses SQLite (with full PostgreSQL compatibility via SQLAlchemy ORM).

### Entities:
* `Student`: `student_id` (PK, e.g. `RTC-STU-0001`), `name`, `department`, `batch_year`.
* `RawEvent`: `event_id` (PK, UNIQUE), `domain`, `student_id`, `event_timestamp`, `arrival_timestamp`, `reporting_date`, `arrival_date`, `batch_id`, `delay_hours`, `is_late`, `is_valid`, `validation_error`, `payload_json`, `processed`.
* `DailyReport`: `report_id` (PK), `reporting_date`, `domain`, `current_version`, `baseline_aggregate`, `corrected_aggregate`, `ground_truth_aggregate`, `baseline_error`, `corrected_error`, `metric_name`, `status`.
* `ReportVersion`: `id` (PK), `report_id`, `version_number`, `aggregate_value`, `change_type`, `created_at`.
* `ReportCorrection`: `correction_id` (PK), `report_id`, `student_id`, `event_id`, `previous_value`, `corrected_value`, `delta_value`, `impact_percentage`, `is_high_impact`, `requires_review`, `status`, `is_rolled_back`.
* `AuditLog`: `log_id` (PK), `timestamp`, `action`, `domain`, `event_id`, `report_id`, `details_json`, `actor`.
* `ExperimentResult`: `experiment_id`, `scenario_name`, `late_event_ratio`, `baseline_mae`, `corrected_mae`, `exact_match_pct`, `processing_time_ms`.

---

## 4. Idempotency & Concurrency Mechanics

1. Primary Key Constraint: `RawEvent.event_id` enforces database-level uniqueness.
2. Ingestion Transaction: Attempting to insert a duplicate `event_id` triggers an `IntegrityError` which is rollbacked, logged to `AuditLog` as `DISCARD_DUPLICATE`, and returned with aggregate contribution +0.
3. Transaction Isolation: SQLite atomic transactions wrap ingestion, version bumping, and audit logging into single atomic operations.
