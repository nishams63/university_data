import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from app.config import settings

DEPARTMENTS = [
    "Computer Science & Engineering",
    "Information Technology",
    "Artificial Intelligence & Data Science",
    "Electronics & Communication Engineering"
]

BATCH_YEARS = [2023, 2024, 2025, 2026]

def generate_synthetic_students(num_students: int = 200, seed: int = 42) -> List[Dict[str, Any]]:
    random.seed(seed)
    students = []
    for i in range(1, num_students + 1):
        student_id = f"RTC-STU-{i:04d}"
        dept = random.choice(DEPARTMENTS)
        batch = random.choice(BATCH_YEARS)
        students.append({
            "student_id": student_id,
            "name": f"Synthetic Student {i:04d}",
            "department": dept,
            "batch_year": batch
        })
    return students

def generate_single_event(
    event_id: str,
    domain: str,
    student_id: str,
    event_datetime: datetime,
    arrival_delay_hours: float,
    batch_id: str = "BATCH-SYNTHETIC",
    is_corrupt: bool = False,
    force_high_impact: bool = False
) -> Dict[str, Any]:
    arrival_datetime = event_datetime + timedelta(hours=arrival_delay_hours)
    
    event_ts_str = event_datetime.strftime("%Y-%m-%dT%H:%M:%S")
    arrival_ts_str = arrival_datetime.strftime("%Y-%m-%dT%H:%M:%S")
    date_str = event_datetime.strftime("%Y-%m-%d")
    
    payload = {}
    if is_corrupt:
        payload = {"invalid_field": None, "malformed": True}
    elif domain == "RTC-Attendance":
        status = "Present" if random.random() > 0.15 else "Absent"
        payload = {
            "attendance_status": status,
            "class_id": random.choice(["CS-301", "IT-204", "AI-102", "EC-405"]),
            "attendance_date": date_str
        }
    elif domain == "RTC-Assessment":
        score = random.uniform(35.0, 98.0)
        is_high_risk = force_high_impact or (random.random() < 0.08)
        payload = {
            "assessment_type": random.choice(["Mid-Term", "End-Sem", "Lab-Assignment"]),
            "subject": random.choice(["Data Structures", "Machine Learning", "VLSI Systems", "Cloud Computing"]),
            "score": round(score, 1),
            "is_high_risk_outcome": is_high_risk
        }
    elif domain == "RTC-Learning":
        payload = {
            "module_id": random.choice(["MOD-101", "MOD-202", "MOD-303", "MOD-404"]),
            "quiz_score": round(random.uniform(50.0, 100.0), 1),
            "access_timestamp": event_ts_str
        }
    elif domain == "RTC-Placement":
        offer_status = "Offered" if random.random() > 0.7 else "Pending"
        is_placement_change = force_high_impact or (offer_status == "Offered")
        payload = {
            "drive_id": random.choice(["DRIVE-GOOGLE", "DRIVE-TCS", "DRIVE-WIPRO", "DRIVE-ZOHO"]),
            "registration_status": "Registered",
            "aptitude_score": round(random.uniform(60.0, 100.0), 1),
            "interview_status": "Passed" if offer_status == "Offered" else "Pending",
            "offer_status": offer_status,
            "is_placement_status_change": is_placement_change
        }

    return {
        "event_id": event_id,
        "domain": domain,
        "student_id": student_id,
        "event_timestamp": event_ts_str,
        "arrival_timestamp": arrival_ts_str,
        "batch_id": batch_id,
        "payload": payload
    }

def generate_synthetic_event_stream(
    num_events: int = 300,
    late_ratio: float = 0.15,
    duplicate_ratio: float = 0.05,
    invalid_ratio: float = 0.02,
    seed: int = 42,
    base_date: datetime = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Returns (students_list, events_list)
    """
    random.seed(seed)
    if base_date is None:
        base_date = datetime(2026, 8, 20, 9, 0, 0)
        
    students = generate_synthetic_students(num_students=100, seed=seed)
    student_ids = [s["student_id"] for s in students]
    
    events = []
    created_event_ids = []
    
    total_late = int(num_events * late_ratio)
    total_duplicates = int(num_events * duplicate_ratio)
    total_invalid = int(num_events * invalid_ratio)
    
    normal_events_count = num_events - total_duplicates - total_invalid
    
    for i in range(1, normal_events_count + 1):
        event_id = f"RTC-EVT-{seed}-{i:05d}"
        domain = random.choice(settings.DOMAINS)
        student_id = random.choice(student_ids)
        
        # Event happened on base_date or up to 5 days prior
        day_offset = random.randint(0, 4)
        event_dt = base_date + timedelta(days=day_offset, hours=random.randint(0, 8))
        
        # Lateness logic
        is_this_late = (i <= total_late)
        if is_this_late:
            # Arrives 26 to 96 hours late (exceeding LATE_THRESHOLD_HOURS=24)
            arrival_delay = random.uniform(26.0, 96.0)
        else:
            # Arrives on-time (0.5 to 12 hours after event)
            arrival_delay = random.uniform(0.5, 12.0)
            
        evt = generate_single_event(
            event_id=event_id,
            domain=domain,
            student_id=student_id,
            event_datetime=event_dt,
            arrival_delay_hours=arrival_delay,
            batch_id=f"BATCH-{seed}"
        )
        events.append(evt)
        created_event_ids.append(evt)
        
    # Inject Duplicates (reuse existing event_ids)
    for d in range(total_duplicates):
        if created_event_ids:
            dup = random.choice(created_event_ids).copy()
            # Arrives in a later batch
            dup_dt = datetime.fromisoformat(dup["arrival_timestamp"]) + timedelta(hours=2)
            dup["arrival_timestamp"] = dup_dt.strftime("%Y-%m-%dT%H:%M:%S")
            dup["batch_id"] = f"BATCH-DUP-{seed}"
            events.append(dup)
            
    # Inject Invalid Events
    for inv in range(1, total_invalid + 1):
        inv_id = f"RTC-EVT-INV-{seed}-{inv:03d}"
        domain = random.choice(settings.DOMAINS)
        student_id = random.choice(student_ids)
        event_dt = base_date + timedelta(days=1)
        evt = generate_single_event(
            event_id=inv_id,
            domain=domain,
            student_id=student_id,
            event_datetime=event_dt,
            arrival_delay_hours=2.0,
            batch_id=f"BATCH-INV-{seed}",
            is_corrupt=True
        )
        events.append(evt)
        
    # Shuffle to simulate out-of-order stream arrival
    random.shuffle(events)
    return students, events
