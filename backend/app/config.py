import os
from pydantic import BaseModel

class Settings(BaseModel):
    INSTITUTION_NAME: str = "RATHINAM TECHNICAL CAMPUS"
    SYSTEM_TITLE: str = "Late-Event Correction & Reporting System"
    DASHBOARD_TITLE: str = "RATHINAM TECHNICAL CAMPUS — Data Quality Dashboard"
    SUBTITLE: str = "Late-Event Correction & Daily Reporting System"
    PRIMARY_STAKEHOLDER: str = "RATHINAM TECHNICAL CAMPUS Data Administrator / Reporting Manager"

    # Configurable Lateness Threshold (hours)
    LATE_THRESHOLD_HOURS: float = float(os.getenv("LATE_THRESHOLD_HOURS", "24.0"))

    # Configurable High Impact Review Threshold (%)
    HIGH_IMPACT_THRESHOLD_PERCENT: float = float(os.getenv("HIGH_IMPACT_THRESHOLD_PERCENT", "15.0"))

    # Random seed for reproducible synthetic generation & experiments
    SEED: int = 42

    # Database connection string
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./rtc_university.db")

    # Data domains
    DOMAINS: list[str] = ["RTC-Learning", "RTC-Assessment", "RTC-Attendance", "RTC-Placement"]

settings = Settings()
