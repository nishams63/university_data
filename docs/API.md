# REST API SPECIFICATION & CONTRACT DOCUMENTATION

**Institution:** Rathinam Technical Campus (Autonomous), Coimbatore  
**Service:** Late-Event Correction & Reporting API  
**Base URL:** `http://localhost:8000/api`  
**API Specification Version:** 1.0.0 (OpenAPI 3.1 compatible)  

---

## 1. Overview & Status Codes

All API endpoints follow RESTful conventions. Responses are returned in standard JSON format.

| HTTP Status Code | Description | Typical Scenario |
| :---: | :--- | :--- |
| **200 OK** | Successful execution | Query results, metrics retrieval, or approved state mutations |
| **201 Created** | Resource created | Event successfully ingested and registered |
| **400 Bad Request** | Business rule or validation error | Invalid review action or malformed transition payload |
| **404 Not Found** | Target resource does not exist | Invalid `report_id` or non-existent `correction_id` |
| **409 Conflict** | Concurrency or uniqueness collision | Duplicate event ID submitted |
| **422 Unprocessable** | Pydantic schema validation failure | Missing required fields or incorrect data types |
| **500 Server Error** | Unexpected unhandled failure | Internal transactional or database engine failure |

---

## 2. System Health, Diagnostics & Watermark

### `GET /api/health`
Returns live system operational status, active threshold policies, and verified SQLite engine PRAGMAs.
- **Response Model:** `HealthCheckResponse`
- **Example Response (200 OK):**
```json
{
  "status": "HEALTHY",
  "institution": "Rathinam Technical Campus (Autonomous), Coimbatore",
  "system": "Late-Event Correction & Daily Reporting System",
  "late_threshold_hours": 24.0,
  "high_impact_threshold_percent": 15.0,
  "mode": "Simulation Mode — Synthetic Demonstration Data",
  "database": {
    "engine_url": "sqlite:///./rtc_university.db",
    "is_sqlite": true,
    "journal_mode": "wal",
    "busy_timeout": 10000,
    "foreign_keys": 1,
    "synchronous": "normal"
  }
}
```

### `GET /api/watermark`
Exposes the active stateful watermark configuration, calculated timestamps, and lateness counts.
- **Response Model:** `WatermarkStatusResponse`
- **Example Response (200 OK):**
```json
{
  "institution_name": "RATHINAM TECHNICAL CAMPUS",
  "watermark_delay_hours": 24.0,
  "late_threshold_hours": 24.0,
  "latest_event_timestamp": "2026-08-25T14:30:00Z",
  "current_watermark_timestamp": "2026-08-24T14:30:00Z",
  "system_time": "2026-09-28T15:28:03.441793+00:00",
  "total_events": 1200,
  "late_events_count": 180,
  "on_time_events_count": 1020,
  "max_delay_hours_observed": 142.5,
  "watermark_policy": "Bounded Out-Of-Order Event Ingestion (24h Watermark Window)"
}
```

### `GET /api/metrics/performance`
Serves benchmark execution metrics captured by `scripts/run_benchmarks.py`.
- **Response (200 OK):** JSON payload containing event scaling benchmarks (100 to 5,000 events) and 4-workload historical replay throughput figures.

### `GET /api/metrics/summary`
Returns institutional dashboard counters, overall health score, and ground truth reconciliation match percentages.

---

## 3. Event Ingestion Pipeline

### `POST /api/events/ingest`
Ingests an event payload into the raw event log and synchronously triggers atomic stateful recalculation.
- **Request Body:** `EventIngestRequest`
```json
{
  "event_id": "RTC-EVT-20260822-0042",
  "domain": "RTC-Assessment",
  "student_id": "RTC-STU-0012",
  "event_timestamp": "2026-08-22T09:30:00Z",
  "arrival_timestamp": "2026-08-25T11:45:00Z",
  "batch_id": "BATCH-MANUAL-SYNC",
  "payload": {
    "assessment_type": "Mid-Term",
    "subject": "CS301-Algorithms",
    "score": 88.5,
    "is_high_risk_outcome": false
  }
}
```
- **Responses:**
  - `200 OK`: Event processed (`status: "INGESTED"`, `"DUPLICATE"`, or `"INVALID"`).
  - `400 Bad Request`: Payload validation error.
  - `422 Unprocessable Entity`: Schema malformed.

### `GET /api/events`
Query parameters:
- `domain` (string, optional): Filter by `RTC-Attendance`, `RTC-Assessment`, `RTC-Learning`, `RTC-Placement`.
- `is_late` (boolean, optional): Filter by lateness status.
- `limit` (integer, default 100, max 500).

---

## 4. Reports, Version Lineage & Approvals

### `GET /api/reports`
Retrieves daily reports with dynamic ground truth re-verification.
- **Query Parameters:** `domain` (optional), `date` (optional: YYYY-MM-DD).

### `GET /api/reports/{report_id}/versions`
Fetches the full monotonic version history for a given report.
- **Path Parameter:** `report_id` (e.g., `RTC-RPT-20260820-RTC-Attendance`).
- **Response (200 OK):** Array of `ReportVersionResponse` ordered ascending by `version_number`.
- **Response (404 Not Found):** If report ID is not found.

### `GET /api/reviews/pending`
Lists all unapproved high-impact or high-risk corrections awaiting human-in-the-loop review.

### `POST /api/reviews/action`
Approve or reject a pending correction.
- **Request Body:**
```json
{
  "correction_id": "CORR-20260928152321-00010",
  "action": "APPROVE",
  "reviewer_name": "RTC Data Administrator"
}
```
- **Status Codes:** `200 OK`, `400 Bad Request` (invalid action string or correction already resolved).

### `POST /api/rollback/execute`
Executes an audit-logged compensating rollback for an applied correction.
- **Request Body:**
```json
{
  "correction_id": "CORR-RTC-RPT-20260820-RTC-Assessment",
  "reason": "Administrative correction after course coordinator grade appeal",
  "actor": "RTC Data Administrator"
}
```

---

## 5. Demonstration & Experiments

### `POST /api/demo/run`
Executes the controlled 5-step live demonstration scenario, producing guaranteed late-event ingestion, threshold alerting, and ground truth recovery.

### `GET /api/reconciliation`
Returns real-time mathematical validation confirming `invariant_satisfied: true` and `exact_match_percentage: 100.0`.

### `GET /api/experiments/scenarios`
Returns the 6 evaluation scenario runs with calculated MAE, RMSE, and exact match percentages.
