from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, UniqueConstraint, ForeignKey, Index
from datetime import datetime, timezone
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Student(Base):
    __tablename__ = "students"

    student_id = Column(String, primary_key=True, index=True)  # e.g. RTC-STU-0001
    name = Column(String, nullable=False)                     # Synthetic student name e.g. Student 0001
    department = Column(String, nullable=False, index=True)
    batch_year = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

class RawEvent(Base):
    __tablename__ = "raw_events"

    event_id = Column(String, primary_key=True, index=True)  # Mandatory idempotency key
    domain = Column(String, nullable=False, index=True)      # RTC-Learning, RTC-Assessment, RTC-Attendance, RTC-Placement
    student_id = Column(String, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False, index=True)
    
    event_timestamp = Column(String, nullable=False, index=True)       # ISO format: university activity time
    arrival_timestamp = Column(String, nullable=False, index=True)     # ISO format: central RTC system receipt time
    processing_timestamp = Column(String, nullable=True)               # ISO format: engine processing time
    
    reporting_date = Column(String, nullable=False, index=True)        # Derived from event_timestamp (YYYY-MM-DD)
    arrival_date = Column(String, nullable=False, index=True)          # Derived from arrival_timestamp (YYYY-MM-DD)
    
    batch_id = Column(String, nullable=False, index=True)
    delay_hours = Column(Float, nullable=False)
    is_late = Column(Boolean, nullable=False, default=False, index=True)
    is_valid = Column(Boolean, nullable=False, default=True, index=True)
    validation_error = Column(String, nullable=True)
    
    payload_json = Column(Text, nullable=False)  # Domain specific JSON payload
    processed = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('event_id', name='uq_event_id'),
        Index('ix_raw_events_date_domain_valid', 'reporting_date', 'domain', 'is_valid'),
        Index('ix_raw_events_arrival_date_domain', 'arrival_date', 'domain'),
    )

class DailyReport(Base):
    __tablename__ = "daily_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String, unique=True, nullable=False, index=True)  # e.g. RTC-RPT-20260820-RTC-Attendance
    reporting_date = Column(String, nullable=False, index=True)         # YYYY-MM-DD
    domain = Column(String, nullable=False, index=True)
    
    current_version = Column(Integer, nullable=False, default=1)
    baseline_aggregate = Column(Float, nullable=False, default=0.0)      # Arrival date snapshot aggregate
    corrected_aggregate = Column(Float, nullable=False, default=0.0)     # Event date dynamic aggregate
    ground_truth_aggregate = Column(Float, nullable=False, default=0.0)  # Independent ground truth aggregate
    
    baseline_error = Column(Float, nullable=False, default=0.0)
    corrected_error = Column(Float, nullable=False, default=0.0)
    
    metric_name = Column(String, nullable=False, default="primary_metric")
    status = Column(String, nullable=False, default="FINALIZED", index=True)  # FINALIZED, CORRECTED, PENDING_REVIEW
    last_updated = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint('reporting_date', 'domain', name='uq_report_date_domain'),
    )

class ReportVersion(Base):
    __tablename__ = "report_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String, ForeignKey("daily_reports.report_id", ondelete="CASCADE"), nullable=False, index=True)
    reporting_date = Column(String, nullable=False, index=True)
    domain = Column(String, nullable=False, index=True)
    
    version_number = Column(Integer, nullable=False)
    aggregate_value = Column(Float, nullable=False)
    metric_name = Column(String, nullable=False)
    
    change_trigger_event_id = Column(String, nullable=True)
    change_type = Column(String, nullable=False)  # INITIAL, LATE_CORRECTION, ROLLBACK, REVIEW_APPROVAL, ON_TIME_UPDATE
    created_at = Column(DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint('report_id', 'version_number', name='uq_report_version_num'),
        Index('ix_report_versions_report_num', 'report_id', 'version_number'),
    )

class ReportCorrection(Base):
    __tablename__ = "report_corrections"

    correction_id = Column(String, primary_key=True, index=True)  # e.g. CORR-20260827-0001
    report_id = Column(String, ForeignKey("daily_reports.report_id", ondelete="CASCADE"), nullable=False, index=True)
    reporting_date = Column(String, nullable=False, index=True)
    domain = Column(String, nullable=False, index=True)
    student_id = Column(String, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(String, ForeignKey("raw_events.event_id", ondelete="CASCADE"), nullable=False, index=True)
    
    previous_version = Column(Integer, nullable=False)
    new_version = Column(Integer, nullable=False)
    previous_value = Column(Float, nullable=False)
    corrected_value = Column(Float, nullable=False)
    delta_value = Column(Float, nullable=False)
    impact_percentage = Column(Float, nullable=False)
    
    is_high_impact = Column(Boolean, nullable=False, default=False, index=True)
    requires_review = Column(Boolean, nullable=False, default=False, index=True)
    reason = Column(String, nullable=False)
    status = Column(String, nullable=False, default="AUTO_CORRECTED", index=True)  # AUTO_CORRECTED, PENDING_REVIEW, APPROVED, REJECTED, ROLLED_BACK
    
    created_at = Column(DateTime, default=utc_now, nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String, nullable=True)
    is_rolled_back = Column(Boolean, nullable=False, default=False, index=True)

    __table_args__ = (
        Index('ix_corrections_report_status', 'report_id', 'status'),
    )

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String, unique=True, nullable=False, index=True)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)
    
    action = Column(String, nullable=False, index=True)  # INGEST_EVENT, DISCARD_DUPLICATE, DISCARD_INVALID, APPLY_CORRECTION, QUEUE_FOR_REVIEW, APPROVE_CORRECTION, REJECT_CORRECTION, ROLLBACK_EXECUTED
    domain = Column(String, nullable=False, index=True)
    event_id = Column(String, nullable=True, index=True)
    report_id = Column(String, nullable=True, index=True)
    correction_id = Column(String, nullable=True, index=True)
    
    details_json = Column(Text, nullable=False)
    actor = Column(String, nullable=False, default="CORRECTION_ENGINE")

class ExperimentResult(Base):
    __tablename__ = "experiment_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String, nullable=False, index=True)
    scenario_name = Column(String, nullable=False)
    late_event_ratio = Column(Float, nullable=False)
    
    total_events = Column(Integer, nullable=False)
    on_time_events_count = Column(Integer, nullable=False)
    late_events_count = Column(Integer, nullable=False)
    duplicate_events_count = Column(Integer, nullable=False)
    invalid_events_count = Column(Integer, nullable=False)
    
    baseline_mae = Column(Float, nullable=False)
    corrected_mae = Column(Float, nullable=False)
    baseline_rmse = Column(Float, nullable=False)
    corrected_rmse = Column(Float, nullable=False)
    exact_match_pct = Column(Float, nullable=False)
    processing_time_ms = Column(Float, nullable=False)
    
    created_at = Column(DateTime, default=utc_now, nullable=False)
