from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, UniqueConstraint, ForeignKey
from datetime import datetime
from app.database import Base

class Student(Base):
    __tablename__ = "students"

    student_id = Column(String, primary_key=True, index=True) # e.g. RTC-STU-0001
    name = Column(String, nullable=False) # Synthetic student name e.g. Student 0001
    department = Column(String, nullable=False)
    batch_year = Column(Integer, nullable=False)

class RawEvent(Base):
    __tablename__ = "raw_events"

    event_id = Column(String, primary_key=True, index=True) # Mandatory idempotency key
    domain = Column(String, nullable=False, index=True) # RTC-Learning, RTC-Assessment, RTC-Attendance, RTC-Placement
    student_id = Column(String, ForeignKey("students.student_id"), nullable=False, index=True)
    
    event_timestamp = Column(String, nullable=False, index=True) # ISO format: university activity time
    arrival_timestamp = Column(String, nullable=False, index=True) # ISO format: central RTC system receipt time
    processing_timestamp = Column(String, nullable=True) # ISO format: engine processing time
    
    reporting_date = Column(String, nullable=False, index=True) # Derived from event_timestamp (YYYY-MM-DD)
    arrival_date = Column(String, nullable=False, index=True) # Derived from arrival_timestamp (YYYY-MM-DD)
    
    batch_id = Column(String, nullable=False)
    delay_hours = Column(Float, nullable=False)
    is_late = Column(Boolean, nullable=False, default=False)
    is_valid = Column(Boolean, nullable=False, default=True)
    validation_error = Column(String, nullable=True)
    
    payload_json = Column(Text, nullable=False) # Domain specific JSON payload
    processed = Column(Boolean, nullable=False, default=False)
    
    __table_args__ = (
        UniqueConstraint('event_id', name='uq_event_id'),
    )

class DailyReport(Base):
    __tablename__ = "daily_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String, unique=True, nullable=False, index=True) # e.g. RTC-RPT-20260820-RTC-Attendance
    reporting_date = Column(String, nullable=False, index=True) # YYYY-MM-DD
    domain = Column(String, nullable=False, index=True)
    
    current_version = Column(Integer, nullable=False, default=1)
    baseline_aggregate = Column(Float, nullable=False, default=0.0) # Arrival date snapshot aggregate
    corrected_aggregate = Column(Float, nullable=False, default=0.0) # Event date dynamic aggregate
    ground_truth_aggregate = Column(Float, nullable=False, default=0.0) # Independent ground truth aggregate
    
    baseline_error = Column(Float, nullable=False, default=0.0)
    corrected_error = Column(Float, nullable=False, default=0.0)
    
    metric_name = Column(String, nullable=False, default="primary_metric")
    status = Column(String, nullable=False, default="FINALIZED") # FINALIZED, CORRECTED, PENDING_REVIEW
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ReportVersion(Base):
    __tablename__ = "report_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String, nullable=False, index=True)
    reporting_date = Column(String, nullable=False, index=True)
    domain = Column(String, nullable=False, index=True)
    
    version_number = Column(Integer, nullable=False)
    aggregate_value = Column(Float, nullable=False)
    metric_name = Column(String, nullable=False)
    
    change_trigger_event_id = Column(String, nullable=True)
    change_type = Column(String, nullable=False) # INITIAL, LATE_CORRECTION, ROLLBACK, REVIEW_APPROVAL
    created_at = Column(DateTime, default=datetime.utcnow)

class ReportCorrection(Base):
    __tablename__ = "report_corrections"

    correction_id = Column(String, primary_key=True, index=True) # e.g. CORR-20260827-0001
    report_id = Column(String, nullable=False, index=True)
    reporting_date = Column(String, nullable=False, index=True)
    domain = Column(String, nullable=False, index=True)
    student_id = Column(String, nullable=False)
    event_id = Column(String, nullable=False)
    
    previous_version = Column(Integer, nullable=False)
    new_version = Column(Integer, nullable=False)
    previous_value = Column(Float, nullable=False)
    corrected_value = Column(Float, nullable=False)
    delta_value = Column(Float, nullable=False)
    impact_percentage = Column(Float, nullable=False)
    
    is_high_impact = Column(Boolean, nullable=False, default=False)
    requires_review = Column(Boolean, nullable=False, default=False)
    reason = Column(String, nullable=False)
    status = Column(String, nullable=False, default="AUTO_CORRECTED") # AUTO_CORRECTED, PENDING_REVIEW, APPROVED, REJECTED, ROLLED_BACK
    
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String, nullable=True)
    is_rolled_back = Column(Boolean, nullable=False, default=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String, unique=True, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    action = Column(String, nullable=False, index=True) # INGEST_EVENT, DISCARD_DUPLICATE, DISCARD_INVALID, APPLY_CORRECTION, QUEUE_FOR_REVIEW, APPROVE_CORRECTION, REJECT_CORRECTION, ROLLBACK_CORRECTION
    domain = Column(String, nullable=False, index=True)
    event_id = Column(String, nullable=True)
    report_id = Column(String, nullable=True)
    correction_id = Column(String, nullable=True)
    
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
    
    created_at = Column(DateTime, default=datetime.utcnow)
