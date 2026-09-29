# API Contracts & OpenAPI Specifications
**Project:** Late-Event Correction & Daily Reporting System  
**Institution:** Rathinam Technical Campus (Autonomous), Coimbatore  
**Milestone:** Review 3 Academic Specification (API Quality & Contracts)  
**Standard:** OpenAPI 3.0 / FastAPI with Explicit Pydantic Models  

---

## 1. Overview & Standard HTTP Status Codes

All API endpoints follow strict REST conventions, explicit Pydantic request and response models, and standardized HTTP status codes:

| HTTP Status Code | Meaning | Usage in RTC System |
|---|---|---|
| **200 OK** | Success | Query results, successful event ingest, approved reviews, completed rollbacks. |
| **201 Created** | Resource Created | New entity creation. |
| **400 Bad Request** | Invalid Operation | Malformed payload syntax, missing required fields. |
| **404 Not Found** | Missing Resource | Report ID or Correction ID does not exist in database. |
| **409 Conflict** | State Transition Conflict | Duplicate rollback attempt, approving already approved correction, or illegal state transition. |
| **422 Unprocessable Entity**| Validation Error | Pydantic validation failure (e.g. non-numeric score, invalid date format). |
| **500 Internal Error** | Server Error | Unhandled runtime exception (stack traces stripped from response). |

---

## 2. Core API Endpoint Contracts

### 2.1 Root Health Check
- **Route:** `GET /health`
- **Tag:** `Observability`
- **Summary:** Standard Root Health & Engine Diagnostics

#### Request
```http
GET /health HTTP/1.1
Host: localhost:8000
Accept: application/json
```

#### Response (200 OK)
```json
{
  "status": "healthy",
  "database": "connected",
  "journal_mode": "wal",
  "foreign_keys": true,
  "busy_timeout_ms": 10000,
  "institution": "RATHINAM TECHNICAL CAMPUS (AUTONOMOUS)"
}
```

---

### 2.2 Event Ingestion
- **Route:** `POST /api/events/ingest`
- **Tag:** `Events`
- **Summary:** Ingest Raw University Event (Atomic Transaction)

#### Request (On-Time Attendance Event)
```json
{
  "event_id": "RTC-EVT-20260820-0012",
  "domain": "RTC-Attendance",
  "student_id": "RTC-STU-0042",
  "event_timestamp": "2026-08-20T08:30:00",
  "arrival_timestamp": "2026-08-20T08:45:00",
  "batch_id": "BATCH-MORNING-ATT",
  "payload": {
    "attendance_status": "Present",
    "class_id": "CS-301",
    "attendance_date": "2026-08-20"
  }
}
```

#### Response (200 OK — Normal Ingest)
```json
{
  "status": "INGESTED",
  "event_id": "RTC-EVT-20260820-0012",
  "reporting_date": "2026-08-20",
  "is_late": false,
  "is_valid": true,
  "message": null,
  "correction_result": {
    "status": "PROCESSED",
    "report_id": "RTC-RPT-20260820-RTC-Attendance",
    "is_high_impact": false,
    "requires_review": false,
    "previous_val": 41.0,
    "new_val": 42.0,
    "correction_id": "CORR-20260820084500-00012"
  }
}
```

#### Request (Duplicate Event Attempt)
```json
{
  "event_id": "RTC-EVT-20260820-0012",
  "domain": "RTC-Attendance",
  "student_id": "RTC-STU-0042",
  "event_timestamp": "2026-08-20T08:30:00",
  "arrival_timestamp": "2026-08-20T09:00:00",
  "batch_id": "BATCH-RETRY-02",
  "payload": {
    "attendance_status": "Present",
    "class_id": "CS-301",
    "attendance_date": "2026-08-20"
  }
}
```

#### Response (200 OK — Idempotent Duplicate Discard)
```json
{
  "status": "DUPLICATE",
  "event_id": "RTC-EVT-20260820-0012",
  "reporting_date": null,
  "is_late": false,
  "is_valid": false,
  "message": "Duplicate event discarded; zero aggregate contribution.",
  "correction_result": null
}
```

---

### 2.3 Watermark & Lateness Status
- **Route:** `GET /api/watermark`
- **Tag:** `Watermark`
- **Summary:** Watermark Status & Lateness Diagnostics

#### Response (200 OK)
```json
{
  "institution_name": "RATHINAM TECHNICAL CAMPUS (AUTONOMOUS)",
  "watermark_delay_hours": 24.0,
  "late_threshold_hours": 24.0,
  "latest_event_timestamp": "2026-08-24T18:00:00+00:00",
  "current_watermark_timestamp": "2026-08-23T18:00:00+00:00",
  "system_time": "2026-09-29T04:45:00.000000+00:00",
  "total_events": 1250,
  "late_events_count": 210,
  "on_time_events_count": 1040,
  "max_delay_hours_observed": 168.0,
  "watermark_policy": "Bounded Out-Of-Order Event Ingestion (24h Watermark Window)"
}
```

---

### 2.4 Pending Reviews Queue
- **Route:** `GET /api/reviews/pending`
- **Tag:** `Human Governance`
- **Summary:** List Pending High-Impact Corrections

#### Response (200 OK)
```json
[
  {
    "correction_id": "CORR-20260824090000-00099",
    "report_id": "RTC-RPT-20260820-RTC-Attendance",
    "reporting_date": "2026-08-20",
    "domain": "RTC-Attendance",
    "student_id": "RTC-STU-0099",
    "event_id": "RTC-EVT-20260820-00099",
    "previous_version": 2,
    "new_version": 3,
    "previous_value": 30.0,
    "corrected_value": 36.0,
    "delta_value": 6.0,
    "impact_percentage": 20.0,
    "is_high_impact": true,
    "requires_review": true,
    "reason": "Late event causing high-impact metric change (20.0% drift)",
    "status": "PENDING_REVIEW",
    "created_at": "2026-08-24T09:00:00",
    "reviewed_at": null,
    "reviewed_by": null,
    "is_rolled_back": false,
    "event_timestamp": "2026-08-20T09:00:00",
    "arrival_timestamp": "2026-08-24T09:00:00",
    "delay_hours": 96.0,
    "dynamic_explanation": "This Attendance event arrived 96.0 hours late and changes the historical aggregate from 30.0 to 36.0 (delta +6). The resulting 20.0% impact exceeds the configured 15% review threshold."
  }
]
```

---

### 2.5 Review Action (Approval / Rejection)
- **Route:** `POST /api/reviews/action`
- **Tag:** `Human Governance`
- **Summary:** Approve or Reject Pending Correction

#### Request (Approve)
```json
{
  "correction_id": "CORR-20260824090000-00099",
  "action": "APPROVE",
  "reviewer_name": "Dr. K. Swaminathan (Dean)",
  "reason": "Verified against physical laboratory attendance register"
}
```

#### Response (200 OK — Successful Approval)
```json
{
  "status": "APPROVED",
  "correction_id": "CORR-20260824090000-00099",
  "action": "APPROVE",
  "new_version": 3,
  "aggregate": 36.0,
  "message": null,
  "reviewer_name": "Dr. K. Swaminathan (Dean)"
}
```

#### Response (409 Conflict — Attempting to re-approve already approved correction)
```json
{
  "detail": "Correction CORR-20260824090000-00099 already approved"
}
```

---

### 2.6 Compensating Rollback
- **Route:** `POST /api/rollback/execute`
- **Tag:** `Rollback`
- **Summary:** Execute Compensating Rollback

#### Request
```json
{
  "correction_id": "CORR-20260824090000-00099",
  "reason": "Administrative correction appeal granted by Controller of Examinations",
  "actor": "RTC Data Administrator"
}
```

#### Response (200 OK — Successful Rollback)
```json
{
  "status": "ROLLED_BACK",
  "correction_id": "CORR-20260824090000-00099",
  "report_id": "RTC-RPT-20260820-RTC-Attendance",
  "previous_val": 36.0,
  "restored_val": 30.0,
  "new_version": 4,
  "message": "Successfully executed compensating rollback for correction CORR-20260824090000-00099."
}
```

#### Response (409 Conflict — Duplicate Rollback Attempt)
```json
{
  "detail": "Correction CORR-20260824090000-00099 has already been rolled back. Operation is idempotent."
}
```

---

### 2.7 Independent Ground-Truth Reconciliation
- **Route:** `GET /api/reconciliation`
- **Tag:** `Reconciliation`
- **Summary:** Ground-Truth Reconciliation Verification

#### Response (200 OK)
```json
{
  "institution": "RATHINAM TECHNICAL CAMPUS (AUTONOMOUS)",
  "total_reporting_dates": 20,
  "matching_dates": 20,
  "mismatching_dates": 0,
  "exact_match_percentage": 100.0,
  "total_absolute_error": 0.0,
  "mean_absolute_error": 0.0,
  "invariant_satisfied": true,
  "mismatches": [],
  "evaluated_at": "2026-09-29T04:48:17.954525+00:00"
}
```

---

### 2.8 System Overview Metrics
- **Route:** `GET /api/metrics`
- **Tag:** `Observability`
- **Summary:** System Overview Metrics

#### Response (200 OK)
```json
{
  "institution_name": "RATHINAM TECHNICAL CAMPUS",
  "overall_health_pct": 100.0,
  "ground_truth_match_pct": 100.0,
  "total_events": 200,
  "on_time_events": 160,
  "late_events": 40,
  "duplicate_events": 8,
  "invalid_events": 2,
  "corrected_reports": 15,
  "pending_reviews": 0,
  "corrections_today": 12,
  "late_threshold_hours": 24.0,
  "high_impact_threshold_pct": 15.0
}
```
