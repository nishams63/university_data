import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import RawEvent, DailyReport, ReportVersion, ReportCorrection, AuditLog
from app.config import settings

def extract_event_metric_contribution(domain: str, payload: dict) -> float:
    """
    Returns numeric value contribution of a single valid event payload.
    """
    if domain == "RTC-Attendance":
        # 1.0 for Present, 0.0 for Absent/Late_Leave
        return 1.0 if payload.get("attendance_status") == "Present" else 0.0
    elif domain == "RTC-Assessment":
        return float(payload.get("score", 0.0))
    elif domain == "RTC-Learning":
        return float(payload.get("quiz_score", 0.0))
    elif domain == "RTC-Placement":
        # 1.0 for Offered, 0.0 otherwise
        return 1.0 if payload.get("offer_status") == "Offered" else 0.0
    return 1.0

def get_domain_metric_name(domain: str) -> str:
    metric_names = {
        "RTC-Attendance": "present_students_count",
        "RTC-Assessment": "total_assessment_marks",
        "RTC-Learning": "total_quiz_points",
        "RTC-Placement": "total_offers_count"
    }
    return metric_names.get(domain, "aggregate_metric")

def compute_ground_truth(db: Session, reporting_date: str, domain: str) -> float:
    """
    INDEPENDENT Ground Truth Calculation:
    1. Select valid events (is_valid == True).
    2. Filter strictly by reporting_date derived from event_timestamp.
    3. Distinct by event_id (deduplication).
    4. Compute expected aggregate sum.
    Does NOT use production correction structures or caches.
    """
    valid_events = db.query(RawEvent).filter(
        RawEvent.reporting_date == reporting_date,
        RawEvent.domain == domain,
        RawEvent.is_valid == True
    ).all()

    # Deduplicate strictly by event_id in memory (in case of raw table query)
    seen_ids = set()
    total_val = 0.0
    for evt in valid_events:
        if evt.event_id not in seen_ids:
            seen_ids.add(evt.event_id)
            payload = json.loads(evt.payload_json)
            total_val += extract_event_metric_contribution(domain, payload)

    return round(total_val, 2)

def compute_naive_baseline(db: Session, arrival_date: str, domain: str) -> float:
    """
    NAIVE Baseline Snapshot Calculation:
    Simulates a traditional system that assigns events to arrival_date.
    Ignores late events that arrive after arrival_date.
    """
    baseline_events = db.query(RawEvent).filter(
        RawEvent.arrival_date == arrival_date,
        RawEvent.domain == domain,
        RawEvent.is_valid == True
    ).all()

    seen_ids = set()
    total_val = 0.0
    for evt in baseline_events:
        if evt.event_id not in seen_ids:
            seen_ids.add(evt.event_id)
            payload = json.loads(evt.payload_json)
            total_val += extract_event_metric_contribution(domain, payload)

    return round(total_val, 2)

def process_and_apply_corrections(db: Session, raw_event_id: str) -> dict:
    """
    Core Stateful Correction Engine:
    1. Fetch ingested raw event.
    2. Check if valid and not yet processed.
    3. Re-calculate dynamic aggregate for target reporting_date.
    4. Compute independent ground truth and naive baseline.
    5. Evaluate impact percentage and check for forced high-risk reviews.
    6. Update DailyReport, create ReportVersion, ReportCorrection, and AuditLog atomically.
    """
    raw_evt = db.query(RawEvent).filter(RawEvent.event_id == raw_event_id).first()
    if not raw_evt or not raw_evt.is_valid:
        return {"status": "SKIPPED", "reason": "Event not found or invalid"}

    reporting_date = raw_evt.reporting_date
    domain = raw_evt.domain
    payload = json.loads(raw_evt.payload_json)
    metric_name = get_domain_metric_name(domain)

    # Fetch or create DailyReport record
    report = db.query(DailyReport).filter(
        DailyReport.reporting_date == reporting_date,
        DailyReport.domain == domain
    ).first()

    if not report:
        report = DailyReport(
            report_id=f"RTC-RPT-{reporting_date.replace('-', '')}-{domain}",
            reporting_date=reporting_date,
            domain=domain,
            current_version=1,
            metric_name=metric_name,
            baseline_aggregate=0.0,
            corrected_aggregate=0.0,
            ground_truth_aggregate=0.0,
            baseline_error=0.0,
            corrected_error=0.0,
            status="FINALIZED"
        )
        db.add(report)
        db.flush()

        # Create initial Version 1 entry
        initial_version = ReportVersion(
            report_id=report.report_id,
            reporting_date=reporting_date,
            domain=domain,
            version_number=1,
            aggregate_value=0.0,
            metric_name=metric_name,
            change_trigger_event_id=raw_event_id,
            change_type="INITIAL"
        )
        db.add(initial_version)

    old_aggregate = report.corrected_aggregate
    
    # Calculate new corrected aggregate (all valid events for this reporting_date so far)
    all_valid_events = db.query(RawEvent).filter(
        RawEvent.reporting_date == reporting_date,
        RawEvent.domain == domain,
        RawEvent.is_valid == True
    ).all()

    new_aggregate = 0.0
    for evt in all_valid_events:
        p = json.loads(evt.payload_json)
        new_aggregate += extract_event_metric_contribution(domain, p)
    new_aggregate = round(new_aggregate, 2)

    # Ground truth & Baseline metrics
    ground_truth_val = compute_ground_truth(db, reporting_date, domain)
    baseline_val = compute_naive_baseline(db, reporting_date, domain)

    delta_val = round(new_aggregate - old_aggregate, 2)

    # Impact calculation (Instruction 10 & 11: distinguish single late events from high-impact batch corrections)
    if old_aggregate == 0.0:
        impact_pct = 0.0 # Initial event creating a new date report is not metric drift
    else:
        impact_pct = round(abs(new_aggregate - old_aggregate) / max(abs(old_aggregate), 10.0) * 100.0, 2)

    # Forced review check for high-risk academic/placement status changes
    forced_review = (
        payload.get("is_high_risk_outcome", False) or 
        payload.get("is_placement_status_change", False) or
        (domain == "RTC-Placement" and payload.get("offer_status") == "Offered")
    )

    # High impact requires >= 15% drift AND absolute delta >= 5.0 (or forced status change)
    is_high_impact = (impact_pct >= settings.HIGH_IMPACT_THRESHOLD_PERCENT and abs(delta_val) >= 5.0) or forced_review
    requires_review = is_high_impact and raw_evt.is_late # Late high-impact changes require review

    correction_id = f"CORR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{raw_evt.event_id[-5:]}"

    if requires_review:
        # High impact: Queue for Data Administrator review
        corr_status = "PENDING_REVIEW"
        report.status = "PENDING_REVIEW"
        
        correction = ReportCorrection(
            correction_id=correction_id,
            report_id=report.report_id,
            reporting_date=reporting_date,
            domain=domain,
            student_id=raw_evt.student_id,
            event_id=raw_evt.event_id,
            previous_version=report.current_version,
            new_version=report.current_version + 1,
            previous_value=old_aggregate,
            corrected_value=new_aggregate,
            delta_value=delta_val,
            impact_percentage=impact_pct,
            is_high_impact=True,
            requires_review=True,
            reason=f"Late event causing high-impact metric change ({impact_pct}% drift)" if not forced_review else "Forced review: High-risk academic/placement status change",
            status="PENDING_REVIEW"
        )
        db.add(correction)

        audit_entry = AuditLog(
            log_id=f"LOG-REV-{correction_id}",
            action="QUEUE_FOR_REVIEW",
            domain=domain,
            event_id=raw_evt.event_id,
            report_id=report.report_id,
            correction_id=correction_id,
            details_json=json.dumps({
                "impact_pct": impact_pct,
                "previous_val": old_aggregate,
                "proposed_val": new_aggregate,
                "reason": correction.reason
            }),
            actor="CORRECTION_ENGINE"
        )
        db.add(audit_entry)

    else:
        # Auto-correct (Low/Medium impact or non-late event)
        new_version_num = report.current_version + 1
        report.current_version = new_version_num
        report.corrected_aggregate = new_aggregate
        report.baseline_aggregate = baseline_val
        report.ground_truth_aggregate = ground_truth_val
        report.baseline_error = round(abs(baseline_val - ground_truth_val), 2)
        report.corrected_error = round(abs(new_aggregate - ground_truth_val), 2)
        report.status = "CORRECTED" if raw_evt.is_late else "FINALIZED"

        # Create Version Record
        version_rec = ReportVersion(
            report_id=report.report_id,
            reporting_date=reporting_date,
            domain=domain,
            version_number=new_version_num,
            aggregate_value=new_aggregate,
            metric_name=metric_name,
            change_trigger_event_id=raw_evt.event_id,
            change_type="LATE_CORRECTION" if raw_evt.is_late else "ON_TIME_UPDATE"
        )
        db.add(version_rec)

        correction = ReportCorrection(
            correction_id=correction_id,
            report_id=report.report_id,
            reporting_date=reporting_date,
            domain=domain,
            student_id=raw_evt.student_id,
            event_id=raw_evt.event_id,
            previous_version=report.current_version - 1,
            new_version=new_version_num,
            previous_value=old_aggregate,
            corrected_value=new_aggregate,
            delta_value=delta_val,
            impact_percentage=impact_pct,
            is_high_impact=is_high_impact,
            requires_review=False,
            reason="Automated late-event delta correction" if raw_evt.is_late else "On-time event aggregation",
            status="AUTO_CORRECTED"
        )
        db.add(correction)

        audit_entry = AuditLog(
            log_id=f"LOG-CORR-{correction_id}",
            action="APPLY_CORRECTION",
            domain=domain,
            event_id=raw_evt.event_id,
            report_id=report.report_id,
            correction_id=correction_id,
            details_json=json.dumps({
                "previous_val": old_aggregate,
                "new_val": new_aggregate,
                "version": new_version_num,
                "is_late": raw_evt.is_late
            }),
            actor="CORRECTION_ENGINE"
        )
        db.add(audit_entry)

    raw_evt.processed = True
    db.commit()

    return {
        "status": "PROCESSED",
        "report_id": report.report_id,
        "is_high_impact": is_high_impact,
        "requires_review": requires_review,
        "previous_val": old_aggregate,
        "new_val": new_aggregate,
        "correction_id": correction_id
    }

def review_pending_correction(db: Session, correction_id: str, action: str, reviewer_name: str = "RTC Data Administrator") -> dict:
    """
    Approves or Rejects a pending high-impact correction.
    """
    corr = db.query(ReportCorrection).filter(ReportCorrection.correction_id == correction_id).first()
    if not corr or corr.status != "PENDING_REVIEW":
        return {"status": "ERROR", "message": "Correction not found or not pending review"}

    report = db.query(DailyReport).filter(DailyReport.report_id == corr.report_id).first()
    
    if action.upper() == "APPROVE":
        corr.status = "APPROVED"
        corr.reviewed_at = datetime.utcnow()
        corr.reviewed_by = reviewer_name

        # Recalculate live aggregate across all valid events for target reporting_date
        live_agg = compute_ground_truth(db, report.reporting_date, report.domain)

        # Increment report version and apply recalculated live value
        new_version_num = report.current_version + 1
        report.current_version = new_version_num
        report.corrected_aggregate = live_agg
        report.ground_truth_aggregate = live_agg
        report.corrected_error = 0.0
        report.status = "CORRECTED"

        # Version Record
        version_rec = ReportVersion(
            report_id=report.report_id,
            reporting_date=report.reporting_date,
            domain=report.domain,
            version_number=new_version_num,
            aggregate_value=live_agg,
            metric_name=report.metric_name,
            change_trigger_event_id=corr.event_id,
            change_type="REVIEW_APPROVAL"
        )
        db.add(version_rec)

        audit_entry = AuditLog(
            log_id=f"LOG-APP-{correction_id}",
            action="APPROVE_CORRECTION",
            domain=report.domain,
            event_id=corr.event_id,
            report_id=report.report_id,
            correction_id=correction_id,
            details_json=json.dumps({
                "approved_by": reviewer_name,
                "new_aggregate": live_agg,
                "version": new_version_num
            }),
            actor=reviewer_name
        )
        db.add(audit_entry)
        db.commit()

        return {"status": "APPROVED", "new_version": new_version_num, "aggregate": live_agg}

    elif action.upper() == "REJECT":
        corr.status = "REJECTED"
        corr.reviewed_at = datetime.utcnow()
        corr.reviewed_by = reviewer_name
        report.status = "CORRECTED"

        audit_entry = AuditLog(
            log_id=f"LOG-REJ-{correction_id}",
            action="REJECT_CORRECTION",
            domain=report.domain,
            event_id=corr.event_id,
            report_id=report.report_id,
            correction_id=correction_id,
            details_json=json.dumps({
                "rejected_by": reviewer_name,
                "proposed_value": corr.corrected_value,
                "kept_value": report.corrected_aggregate
            }),
            actor=reviewer_name
        )
        db.add(audit_entry)
        db.commit()

        return {"status": "REJECTED", "aggregate": report.corrected_aggregate}

    return {"status": "ERROR", "message": "Invalid action; must be APPROVE or REJECT"}
