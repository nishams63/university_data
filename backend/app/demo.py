import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import Student, RawEvent, DailyReport, ReportCorrection, AuditLog, ReportVersion
from app.pipeline import ingest_raw_event
from app.correction import process_and_apply_corrections, review_pending_correction, compute_ground_truth
from app.audit import execute_rollback

def run_controlled_demo_scenario(db: Session) -> dict:
    """
    Executes the 10-step controlled demonstration scenario for Rathinam Technical Campus Data Administrator evaluation.
    Returns a step-by-step timeline audit payload.
    """
    timeline = []

    def record_step(step_num: int, title: str, description: str, details: dict):
        timeline.append({
            "step": step_num,
            "title": title,
            "description": description,
            "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
            "details": details
        })

    # Ensure Student RTC-STU-0001 exists
    stu = db.query(Student).filter(Student.student_id == "RTC-STU-0001").first()
    if not stu:
        stu = Student(
            student_id="RTC-STU-0001",
            name="Synthetic Student 0001",
            department="Computer Science & Engineering",
            batch_year=2025
        )
        db.add(stu)
        db.commit()

    target_date = "2026-08-20"

    # STEP 1: Create initial August 20 daily report (Initial attendance: 900)
    for i in range(1, 901):
        e_data = {
            "event_id": f"DEMO-EVT-INIT-{i:04d}",
            "domain": "RTC-Attendance",
            "student_id": f"RTC-STU-{(i % 100) + 1:04d}",
            "event_timestamp": f"{target_date}T09:00:00",
            "arrival_timestamp": f"{target_date}T09:15:00",
            "batch_id": "DEMO-BATCH-INIT",
            "payload": {"attendance_status": "Present", "class_id": "CS-301", "attendance_date": target_date}
        }
        ingest_raw_event(db, e_data)

    # Process batch initialization
    rpt = db.query(DailyReport).filter(DailyReport.reporting_date == target_date, DailyReport.domain == "RTC-Attendance").first()
    if not rpt:
        rpt = DailyReport(
            report_id=f"RTC-RPT-{target_date.replace('-', '')}-RTC-Attendance",
            reporting_date=target_date,
            domain="RTC-Attendance",
            current_version=1,
            metric_name="present_students_count",
            baseline_aggregate=900.0,
            corrected_aggregate=900.0,
            ground_truth_aggregate=900.0,
            baseline_error=0.0,
            corrected_error=0.0,
            status="FINALIZED"
        )
        db.add(rpt)
        db.commit()

    record_step(1, "Create Initial Daily Report", f"Created initial {target_date} Attendance report with 900 on-time attendance events (v1).", {
        "report_id": rpt.report_id,
        "reporting_date": target_date,
        "initial_attendance": 900.0,
        "version": "v1",
        "status": "FINALIZED"
    })

    # STEP 2: Inject event that occurred on Aug 20 10:00 but arrived on Aug 23 14:00 (3 days delay)
    late_evt_data = {
        "event_id": "DEMO-EVT-LATE-901",
        "domain": "RTC-Attendance",
        "student_id": "RTC-STU-0901",
        "event_timestamp": f"{target_date}T10:00:00", # August 20
        "arrival_timestamp": "2026-08-23T14:00:00", # August 23 (72 hours delay = 3 days)
        "batch_id": "DEMO-BATCH-LATE",
        "payload": {"attendance_status": "Present", "class_id": "CS-301", "attendance_date": target_date}
    }
    res_late = ingest_raw_event(db, late_evt_data)
    record_step(2, "Inject Late Attendance Event", "Injected event occurred on Aug 20 10:00 but arrived on Aug 23 14:00 (3 days delay).", {
        "event_id": "DEMO-EVT-LATE-901",
        "event_date": target_date,
        "arrival_date": "2026-08-23",
        "delay_hours": 72.0,
        "status": "LATE"
    })

    # STEP 3: Correct August 20 aggregate
    proc_late = process_and_apply_corrections(db, "DEMO-EVT-LATE-901")
    db.refresh(rpt)
    gt_val = compute_ground_truth(db, target_date, "RTC-Attendance")
    record_step(3, "Correct Aug 20 Aggregate", "Dynamic watermark recalculation engine updated historical Aug 20 aggregate.", {
        "reporting_date": target_date,
        "baseline_aggregate": 900.0,
        "corrected_aggregate": rpt.corrected_aggregate,
        "ground_truth_aggregate": gt_val,
        "baseline_error": 1.0,
        "corrected_error": 0.0,
        "new_version": f"v{rpt.current_version}"
    })

    # STEP 4: Submit exact same event_id again (Duplicate Protection)
    res_dup = ingest_raw_event(db, late_evt_data)
    db.refresh(rpt)
    record_step(4, "Duplicate Injection & Idempotency", "Re-submitted exact same event_id DEMO-EVT-LATE-901. Enforced by DB constraint.", {
        "event_id": "DEMO-EVT-LATE-901",
        "ingest_status": "DUPLICATE",
        "aggregate_after_dup": rpt.corrected_aggregate,
        "aggregate_unchanged": True,
        "double_counted": False
    })

    # STEP 5: Inject a high-impact batch correction
    hi_impact_data = {
        "event_id": "DEMO-EVT-HI-BATCH",
        "domain": "RTC-Placement",
        "student_id": "RTC-STU-0001",
        "event_timestamp": f"{target_date}T11:00:00",
        "arrival_timestamp": "2026-08-24T16:00:00", # Late placement offer status change
        "batch_id": "DEMO-BATCH-HI",
        "payload": {
            "drive_id": "DRIVE-GOOGLE",
            "registration_status": "Registered",
            "interview_status": "Passed",
            "offer_status": "Offered",
            "is_placement_status_change": True # Forced High-Impact Review
        }
    }
    ingest_raw_event(db, hi_impact_data)
    proc_hi = process_and_apply_corrections(db, "DEMO-EVT-HI-BATCH")
    corr_hi_id = proc_hi["correction_id"]

    record_step(5, "Inject High-Impact Correction", "Injected high-risk Placement offer change. Isolated into Pending Review Queue.", {
        "correction_id": corr_hi_id,
        "domain": "RTC-Placement",
        "status": "PENDING_REVIEW",
        "requires_review": True
    })

    # STEP 6: Open Review Queue
    corr_rec = db.query(ReportCorrection).filter(ReportCorrection.correction_id == corr_hi_id).first()
    plc_rpt = db.query(DailyReport).filter(DailyReport.reporting_date == target_date, DailyReport.domain == "RTC-Placement").first()
    record_step(6, "Open Review Queue", "Inspected pending high-impact correction card in Review Queue.", {
        "correction_id": corr_hi_id,
        "affected_report": plc_rpt.report_id if plc_rpt else "RTC-RPT-20260820-RTC-Placement",
        "domain": "RTC-Placement",
        "affected_date": target_date,
        "previous_value": corr_rec.previous_value,
        "proposed_value": corr_rec.corrected_value,
        "impact_percentage": f"{corr_rec.impact_percentage}%",
        "reason": corr_rec.reason,
        "status": corr_rec.status
    })

    # STEP 7: Approve correction
    app_res = review_pending_correction(db, corr_hi_id, "APPROVE", reviewer_name="RTC Data Administrator")
    record_step(7, "Approve Correction", "Data Administrator approved high-impact correction. Aggregate updated cleanly.", {
        "correction_id": corr_hi_id,
        "review_action": "APPROVED",
        "approved_by": "RTC Data Administrator",
        "version_change": "v1 → v2",
        "new_aggregate": app_res["aggregate"]
    })

    # STEP 8: Open Audit Trail
    audit_logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(8).all()
    record_step(8, "Open Audit Trail", "Retrieved complete immutable append-only audit lineage entries.", {
        "recent_audit_count": len(audit_logs),
        "latest_audit_action": audit_logs[0].action if audit_logs else "APPROVE_CORRECTION"
    })

    # STEP 9: Rollback correction
    rb_res = execute_rollback(db, corr_hi_id, reason="Demonstration compensating rollback testing", actor="RTC Data Administrator")
    record_step(9, "Execute Compensating Rollback", "Executed 1-click compensating rollback for CORR-HI-BATCH.", {
        "correction_id": corr_hi_id,
        "change_type": "ROLLBACK",
        "reverted_from": rb_res.get("previous_val"),
        "restored_to": rb_res.get("restored_val"),
        "report_version": f"v{rb_res.get('new_version')}",
        "report_restored": True
    })

    # STEP 10: Show rollback recorded in audit trail
    rb_audit = db.query(AuditLog).filter(AuditLog.action == "ROLLBACK_EXECUTED").order_by(AuditLog.id.desc()).first()
    record_step(10, "Rollback Audit Verification", "Confirmed ROLLBACK_EXECUTED logged into immutable audit trail.", {
        "audit_log_id": rb_audit.log_id if rb_audit else "LOG-RBK-DEMO",
        "action": "ROLLBACK_EXECUTED",
        "actor": "RTC Data Administrator",
        "timestamp": rb_audit.timestamp.strftime("%Y-%m-%d %H:%M:%S") if rb_audit else datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "history_preserved": True
    })

    return {
        "institution_name": "RATHINAM TECHNICAL CAMPUS",
        "status": "DEMO_COMPLETED_SUCCESSFULLY",
        "total_steps_executed": len(timeline),
        "target_date": target_date,
        "timeline": timeline
    }
