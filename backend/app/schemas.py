from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from datetime import datetime

class StudentBase(BaseModel):
    student_id: str
    name: str
    department: str
    batch_year: int

class StudentResponse(StudentBase):
    class Config:
        from_attributes = True

class EventPayload(BaseModel):
    # Flexible container for domain payloads
    attendance_status: Optional[str] = None # Present, Absent, Late_Leave
    class_id: Optional[str] = None
    attendance_date: Optional[str] = None
    
    assessment_type: Optional[str] = None # Mid-Term, End-Sem, Lab-Assignment
    subject: Optional[str] = None
    score: Optional[float] = None
    is_high_risk_outcome: Optional[bool] = False # e.g. Pass/Fail alteration
    
    module_id: Optional[str] = None
    quiz_score: Optional[float] = None
    access_timestamp: Optional[str] = None
    
    drive_id: Optional[str] = None
    registration_status: Optional[str] = None
    aptitude_score: Optional[float] = None
    interview_status: Optional[str] = None
    offer_status: Optional[str] = None # Selected, Pending, Rejected
    is_placement_status_change: Optional[bool] = False

class EventIngestRequest(BaseModel):
    event_id: str
    domain: str # RTC-Learning, RTC-Assessment, RTC-Attendance, RTC-Placement
    student_id: str
    event_timestamp: str # ISO string
    arrival_timestamp: Optional[str] = None # ISO string (defaults to current time if omitted)
    batch_id: Optional[str] = "BATCH-MANUAL"
    payload: Dict[str, Any]

class RawEventResponse(BaseModel):
    event_id: str
    domain: str
    student_id: str
    event_timestamp: str
    arrival_timestamp: str
    reporting_date: str
    arrival_date: str
    batch_id: str
    delay_hours: float
    is_late: bool
    is_valid: bool
    validation_error: Optional[str] = None
    payload_json: str
    processed: bool

    class Config:
        from_attributes = True

class DailyReportResponse(BaseModel):
    report_id: str
    reporting_date: str
    domain: str
    current_version: int
    metric_name: str
    baseline_aggregate: float
    corrected_aggregate: float
    ground_truth_aggregate: float
    baseline_error: float
    corrected_error: float
    status: str
    last_updated: Optional[datetime] = None

    class Config:
        from_attributes = True

class ReportVersionResponse(BaseModel):
    id: int
    report_id: str
    reporting_date: str
    domain: str
    version_number: int
    aggregate_value: float
    metric_name: str
    change_trigger_event_id: Optional[str] = None
    change_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class ReportCorrectionResponse(BaseModel):
    correction_id: str
    report_id: str
    reporting_date: str
    domain: str
    student_id: str
    event_id: str
    previous_version: int
    new_version: int
    previous_value: float
    corrected_value: float
    delta_value: float
    impact_percentage: float
    is_high_impact: bool
    requires_review: bool
    reason: str
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    is_rolled_back: bool

    class Config:
        from_attributes = True

class ReviewActionRequest(BaseModel):
    correction_id: str
    action: str # APPROVE or REJECT
    reviewer_name: Optional[str] = "RTC Data Administrator"

class RollbackRequest(BaseModel):
    correction_id: str
    reason: Optional[str] = "Data Administrator Manual Rollback"
    actor: Optional[str] = "RTC Data Administrator"

class AuditLogResponse(BaseModel):
    id: int
    log_id: str
    timestamp: datetime
    action: str
    domain: str
    event_id: Optional[str] = None
    report_id: Optional[str] = None
    correction_id: Optional[str] = None
    details_json: str
    actor: str

    class Config:
        from_attributes = True

class SystemMetricsSummary(BaseModel):
    institution_name: str = "RATHINAM TECHNICAL CAMPUS"
    overall_health_pct: float
    ground_truth_match_pct: float
    total_events: int
    on_time_events: int
    late_events: int
    duplicate_events: int
    invalid_events: int
    corrected_reports: int
    pending_reviews: int
    corrections_today: int
    late_threshold_hours: float
    high_impact_threshold_pct: float

class RunExperimentRequest(BaseModel):
    seed: Optional[int] = 42
    total_events_per_scenario: Optional[int] = 200

class ExperimentScenarioResponse(BaseModel):
    experiment_id: str
    scenario_name: str
    late_event_ratio: float
    total_events: int
    on_time_events_count: int
    late_events_count: int
    duplicate_events_count: int
    invalid_events_count: int
    baseline_mae: float
    corrected_mae: float
    baseline_rmse: float
    corrected_rmse: float
    exact_match_pct: float
    processing_time_ms: float
    created_at: datetime

    class Config:
        from_attributes = True
