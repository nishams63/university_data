import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import DailyReport, ReportVersion, ReportCorrection, AuditLog
from app.correction import compute_ground_truth

def execute_rollback(
    db: Session,
    correction_id: str,
    reason: str = "Data Administrator Manual Rollback",
    actor: str = "RTC Data Administrator"
) -> dict:
    """
    Executes a compensating rollback for a target correction.
    Idempotent guard: Prevents rolling back an already rolled-back correction.
    Appends a new report version history record without modifying old history.
    """
    corr = db.query(ReportCorrection).filter(ReportCorrection.correction_id == correction_id).first()
    if not corr:
        return {"status": "ERROR", "message": f"Correction {correction_id} not found."}

    if corr.is_rolled_back or corr.status == "ROLLED_BACK":
        return {
            "status": "ALREADY_ROLLED_BACK",
            "message": f"Correction {correction_id} has already been rolled back. Operation is idempotent.",
            "correction_id": correction_id
        }

    if corr.status not in ["AUTO_CORRECTED", "APPROVED"]:
        return {
            "status": "ERROR",
            "message": f"Cannot rollback correction in state '{corr.status}' (Must be AUTO_CORRECTED or APPROVED)."
        }

    report = db.query(DailyReport).filter(DailyReport.report_id == corr.report_id).first()
    if not report:
        return {"status": "ERROR", "message": f"Associated report {corr.report_id} not found."}

    # Compensating action calculation
    old_agg = report.corrected_aggregate
    restored_agg = round(corr.previous_value, 2)
    
    # Increment version
    new_version_num = report.current_version + 1
    report.current_version = new_version_num
    report.corrected_aggregate = restored_agg

    ground_truth_val = compute_ground_truth(db, report.reporting_date, report.domain)
    report.ground_truth_aggregate = ground_truth_val
    report.corrected_error = round(abs(restored_agg - ground_truth_val), 2)
    report.status = "CORRECTED"

    # Append new Version record to preserve full version lineage
    version_rec = ReportVersion(
        report_id=report.report_id,
        reporting_date=report.reporting_date,
        domain=report.domain,
        version_number=new_version_num,
        aggregate_value=restored_agg,
        metric_name=report.metric_name,
        change_trigger_event_id=corr.event_id,
        change_type="ROLLBACK"
    )
    db.add(version_rec)

    # Mark correction as rolled back
    corr.is_rolled_back = True
    corr.status = "ROLLED_BACK"

    # Create immutable audit log entry
    audit_entry = AuditLog(
        log_id=f"LOG-RBK-{correction_id}-{datetime.utcnow().timestamp()}",
        action="ROLLBACK_EXECUTED",
        domain=report.domain,
        event_id=corr.event_id,
        report_id=report.report_id,
        correction_id=correction_id,
        details_json=json.dumps({
            "reason": reason,
            "reverted_from_val": old_agg,
            "restored_to_val": restored_agg,
            "new_version": new_version_num,
            "actor": actor
        }),
        actor=actor
    )
    db.add(audit_entry)
    db.commit()

    return {
        "status": "ROLLED_BACK",
        "correction_id": correction_id,
        "report_id": report.report_id,
        "previous_val": old_agg,
        "restored_val": restored_agg,
        "new_version": new_version_num,
        "message": f"Successfully executed compensating rollback for correction {correction_id}."
    }
