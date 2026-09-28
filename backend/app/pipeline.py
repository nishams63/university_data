import json
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models import RawEvent, Student, AuditLog
from app.config import settings

logger = logging.getLogger("rtc.pipeline")
logging.basicConfig(level=logging.INFO)

def get_utc_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

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

def ingest_raw_event(db: Session, event_data: dict, auto_commit: bool = True) -> dict:
    """
    Ingests a raw event into the database with idempotency and schema validation.
    Enforces idempotency via database constraints on event_id.
    """
    event_id = event_data["event_id"]
    domain = event_data["domain"]
    student_id = event_data["student_id"]
    event_ts_str = event_data["event_timestamp"]
    arrival_ts_str = event_data.get("arrival_timestamp") or get_utc_iso()
    batch_id = event_data.get("batch_id", "BATCH-MANUAL")
    payload = event_data.get("payload", {})

    logger.info(f"EVENT_RECEIVED: event_id={event_id} domain={domain} student_id={student_id}")

    # Check 1: Idempotency query check
    existing_event = db.query(RawEvent).filter(RawEvent.event_id == event_id).first()
    if existing_event:
        logger.warning(f"EVENT_DUPLICATE: event_id={event_id} already exists in DB.")
        audit_entry = AuditLog(
            log_id=f"LOG-DUP-{event_id}-{int(datetime.now(timezone.utc).timestamp()*1000)}",
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
        if auto_commit:
            db.commit()
        return {
            "status": "DUPLICATE",
            "event_id": event_id,
            "message": "Duplicate event discarded; zero aggregate contribution.",
            "is_late": False,
            "is_valid": False
        }

    # Ensure Student exists in DB with concurrency race protection
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        try:
            student = Student(
                student_id=student_id,
                name=f"Synthetic Student {student_id}",
                department="Computer Science & Engineering",
                batch_year=2025
            )
            db.add(student)
            db.flush()
        except IntegrityError:
            db.rollback()
            student = db.query(Student).filter(Student.student_id == student_id).first()

    # Parse timestamps & calculate lateness
    try:
        event_dt = datetime.fromisoformat(event_ts_str.replace("Z", "+00:00"))
        arrival_dt = datetime.fromisoformat(arrival_ts_str.replace("Z", "+00:00"))
        # Strip tzinfo for consistent naive timedelta math if mixed
        if event_dt.tzinfo is not None and arrival_dt.tzinfo is None:
            arrival_dt = arrival_dt.replace(tzinfo=event_dt.tzinfo)
        elif arrival_dt.tzinfo is not None and event_dt.tzinfo is None:
            event_dt = event_dt.replace(tzinfo=arrival_dt.tzinfo)
    except Exception as e:
        is_valid = False
        val_error = f"Invalid ISO timestamp format: {str(e)}"
        event_dt = datetime.now(timezone.utc)
        arrival_dt = datetime.now(timezone.utc)
    else:
        is_valid, val_error = validate_event_payload(domain, payload)

    reporting_date = event_dt.strftime("%Y-%m-%d")
    arrival_date = arrival_dt.strftime("%Y-%m-%d")
    delay_hours = max((arrival_dt - event_dt).total_seconds() / 3600.0, 0.0)
    is_late = delay_hours > settings.LATE_THRESHOLD_HOURS

    if is_late:
        logger.info(f"EVENT_LATE: event_id={event_id} delay_hours={round(delay_hours, 2)} threshold={settings.LATE_THRESHOLD_HOURS}")

    proc_ts_str = get_utc_iso()

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
        db.flush()  # Flush to trigger DB constraint if concurrent race occurs
    except IntegrityError:
        db.rollback()
        logger.warning(f"EVENT_DUPLICATE: IntegrityError caught for event_id={event_id}")
        audit_entry = AuditLog(
            log_id=f"LOG-DUP-INTEG-{event_id}-{int(datetime.now(timezone.utc).timestamp()*1000)}",
            action="DISCARD_DUPLICATE",
            domain=domain,
            event_id=event_id,
            details_json=json.dumps({"message": f"Duplicate event constraint caught: {event_id}"}),
            actor="SYSTEM_INGESTION"
        )
        db.add(audit_entry)
        if auto_commit:
            db.commit()
        return {
            "status": "DUPLICATE",
            "event_id": event_id,
            "message": "Duplicate event caught by database constraint.",
            "is_late": False,
            "is_valid": False
        }

    if not is_valid:
        logger.warning(f"EVENT_INVALID: event_id={event_id} error={val_error}")
        audit_entry = AuditLog(
            log_id=f"LOG-INV-{event_id}-{int(datetime.now(timezone.utc).timestamp()*1000)}",
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
        if auto_commit:
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
        log_id=f"LOG-INGEST-{event_id}-{int(datetime.now(timezone.utc).timestamp()*1000)}",
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
    
    if auto_commit:
        db.commit()

    return {
        "status": "INGESTED",
        "event_id": event_id,
        "reporting_date": reporting_date,
        "is_late": is_late,
        "is_valid": True,
        "raw_event": raw_event
    }

def ingest_and_process_atomic(db: Session, event_data: dict, max_retries: int = 8) -> dict:
    """
    Executes ingestion, delta recalculation, report update, versioning,
    and audit logging within a SINGLE ATOMIC TRANSACTION boundary.
    Includes concurrency retry with exponential jitter backoff for high-contention report dates.
    If unrecoverable error occurs, rolls back cleanly.
    """
    import time
    import random
    from app.correction import process_and_apply_corrections

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                db.rollback()
                db.expunge_all()

            ingest_res = ingest_raw_event(db, event_data, auto_commit=False)
            
            if ingest_res["status"] == "INGESTED":
                corr_res = process_and_apply_corrections(db, ingest_res["event_id"], auto_commit=False)
                ingest_res["correction_result"] = corr_res
            
            db.commit()
            return ingest_res
        except IntegrityError as ie:
            db.rollback()
            db.expunge_all()
            if attempt < max_retries - 1:
                time.sleep(0.02 * (attempt + 1) + random.uniform(0.01, 0.05))
                continue
            logger.error(f"TRANSACTION_FAILED: event_id={event_data.get('event_id')} after {max_retries} attempts: {str(ie)}")
            raise
        except Exception as e:
            db.rollback()
            db.expunge_all()
            logger.error(f"TRANSACTION_FAILED: event_id={event_data.get('event_id')} error={str(e)}")
            raise
