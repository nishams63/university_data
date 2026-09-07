from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.generator import generate_synthetic_event_stream
from app.pipeline import ingest_raw_event
from app.correction import process_and_apply_corrections
from app.models import Student, RawEvent, DailyReport
from app.database import Base, engine, SessionLocal

def seed_initial_database(num_events: int = 250, seed: int = 42):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if already seeded
        existing_events = db.query(RawEvent).count()
        if existing_events >= 50:
            print(f"[RTC Seed] Database already contains {existing_events} raw events. Skipping seed.")
            return

        print("[RTC Seed] Seeding synthetic data for RATHINAM TECHNICAL CAMPUS...")
        students, events = generate_synthetic_event_stream(
            num_events=num_events,
            late_ratio=0.18,
            duplicate_ratio=0.04,
            invalid_ratio=0.02,
            seed=seed,
            base_date=datetime(2026, 8, 20, 9, 0, 0)
        )

        for evt in events:
            res = ingest_raw_event(db, evt)
            if res["status"] == "INGESTED":
                process_and_apply_corrections(db, res["event_id"])

        total_reports = db.query(DailyReport).count()
        total_evts = db.query(RawEvent).count()
        print(f"[RTC Seed] Seeding completed: {total_evts} raw events, {total_reports} daily reports created.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_initial_database()
