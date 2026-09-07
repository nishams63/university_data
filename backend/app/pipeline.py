import json
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models import RawEvent, Student, AuditLog
from app.config import settings
from app.schemas import EventIngestRequest

def validate_event_payload(domain: str, payload: dict) -> tuple[bool, str]:
    if not isinstance(payload, dict):
        return False, "Payload is not a valid JSON object"
        
    if domain == "RTC-Attendance":
        if "attendance_status" not in payload or payload["attendance_status"] not in ["Present", "Absent", "Late_Leave"]:
            return False, "Missing or invalid attendance_status"
    elif domain == "RTC-Assessment":
        if "score" not in payload or not isinstance(payload["score"], (int, float)):
            return False, "Missing or non-numeric assessment score"
    elif domain == "RTC-Learning":
        if "quiz_score" not in payload or not isinstance(payload["quiz_score"], (int, float)):
            return False, "Missing or non-numeric quiz score"
    elif domain == "RTC-Placement":
        if "offer_status" not in payload:
            return False, "Missing offer_status in placement event payload"
    else:
        return False, f"Unknown domain: {domain}"
        
    return True, ""

def ingest_raw_event(db: Session, event_data: dict) -> dict:
    """
    Ingests a raw event into the database atomically.
    Enforces idempotency via database constraints on event_id.
    Validates schema and classifies lateness based on LATE_THRESHOLD_HOURS.
    """
    event_id = event_data["event_id"]
    domain = event_data["domain"]
    student_id = event_data["student_id"]
    event_ts_str = event_data["event_timestamp"]
    arrival_ts_str = event_data.get("arrival_timestamp") or datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    batch_id = event_data.get("batch_id", "BATCH-MANUAL")
    payload = event_data.get("payload", {})

    # Check 1: Idempotency check via DB query (Fast early check)
    existing_event = db.query(RawEvent).filter(RawEvent.event_id == event_id).first()
    if existing_event:
        # Log duplicate discard audit entry
        audit_entry = AuditLog(
            log_id=f"LOG-DUP-{event_id}-{datetime.utcnow().timestamp()}",
            action="DISCARD_DUPLICATE",
            domain=domain,
            event_id=event_id,
            details_json=json.dumps({
                "message": f"Duplicate event {event_id} received in batch {batch_id}. Contribution +0.",
                "original_batch": existing_event.batch_id,
                "duplicate_batch": batch_id
            }),
            actor="SYSTEM_INGESTION"
        )
        db.add(audit_entry)
        db.commit()
        return {
            "status": "DUPLICATE",
            "event_id": event_id,
            "message": "Duplicate event discarded; zero aggregate contribution.",
            "is_late": False,
            "is_valid": False
        }

    # Ensure Student exists in DB (or create mock student if missing)
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        student = Student(
            student_id=student_id,
            name=f"Synthetic Student {student_id}",
            department="Computer Science & Engineering",
            batch_year=2025
        )
        db.add(student)

    # Parse timestamps & calculate lateness
    try:
        event_dt = datetime.fromisoformat(event_ts_str)
        arrival_dt = datetime.fromisoformat(arrival_ts_str)
    except Exception as e:
        is_valid = False
        val_error = f"Invalid ISO timestamp format: {str(e)}"
        event_dt = datetime.utcnow()
        arrival_dt = datetime.utcnow()
    else:
        is_valid, val_error = validate_event_payload(domain, payload)

    reporting_date = event_dt.strftime("%Y-%m-%d")
    arrival_date = arrival_dt.strftime("%Y-%m-%d")
    delay_hours = (arrival_dt - event_dt).total_seconds() / 3600.0
    is_late = delay_hours > settings.LATE_THRESHOLD_HOURS

    proc_ts_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

    raw_event = RawEvent(
        event_id=event_id,
        domain=domain,
        student_id=student_id,
        event_timestamp=event_ts_str,
        arrival_timestamp=arrival_ts_str,
        processing_timestamp=proc_ts_str,
        reporting_date=reporting_date,
        arrival_date=arrival_date,
        batch_id=batch_id,
        delay_hours=round(delay_hours, 2),
        is_late=is_late,
        is_valid=is_valid,
        validation_error=val_error if not is_valid else None,
        payload_json=json.dumps(payload),
        processed=False
    )

    try:
        db.add(raw_event)
        db.flush() # Flush to hit DB unique constraint
    except IntegrityError:
        db.rollback()
        # Fallback handling for race-condition duplicate constraint hit
        audit_entry = AuditLog(
            log_id=f"LOG-DUP-INTEG-{event_id}-{datetime.utcnow().timestamp()}",
            action="DISCARD_DUPLICATE",
            domain=domain,
            event_id=event_id,
            details_json=json.dumps({"message": f"Duplicate event constraint caught: {event_id}"}),
            actor="SYSTEM_INGESTION"
        )
        db.add(audit_entry)
        db.commit()
        return {
            "status": "DUPLICATE",
            "event_id": event_id,
            "message": "Duplicate event caught by database constraint.",
            "is_late": False,
            "is_valid": False
        }

    if not is_valid:
        audit_entry = AuditLog(
            log_id=f"LOG-INV-{event_id}-{datetime.utcnow().timestamp()}",
            action="DISCARD_INVALID",
            domain=domain,
            event_id=event_id,
            details_json=json.dumps({
                "message": f"Invalid event payload: {val_error}",
                "payload": payload
            }),
            actor="SYSTEM_INGESTION"
        )
        db.add(audit_entry)
        db.commit()
        return {
            "status": "INVALID",
            "event_id": event_id,
            "message": f"Invalid event: {val_error}",
            "is_late": is_late,
            "is_valid": False
        }

    # Log successful ingestion audit log
    audit_entry = AuditLog(
        log_id=f"LOG-INGEST-{event_id}-{datetime.utcnow().timestamp()}",
        action="INGEST_EVENT",
        domain=domain,
        event_id=event_id,
        details_json=json.dumps({
            "reporting_date": reporting_date,
            "arrival_date": arrival_date,
            "delay_hours": round(delay_hours, 2),
            "is_late": is_late
        }),
        actor="SYSTEM_INGESTION"
    )
    db.add(audit_entry)
    db.commit()

    return {
        "status": "INGESTED",
        "event_id": event_id,
        "reporting_date": reporting_date,
        "is_late": is_late,
        "is_valid": True,
        "raw_event": raw_event
    }
