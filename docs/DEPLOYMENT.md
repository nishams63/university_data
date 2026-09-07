# Deployment Guide — RATHINAM TECHNICAL CAMPUS

## 1. Local Development Architecture

The default deployment operates with zero external infrastructure dependencies:
* Backend: Python 3.14 + FastAPI + Uvicorn + SQLite
* Frontend: Node.js 24 + Vite + React 18 + Tailwind CSS

### One-Command Startup (PowerShell / Windows)

Backend Server (Port 8000):
```powershell
cd backend
py -m uvicorn app.main:app --reload --port 8000
```

Frontend Server (Port 3000):
```powershell
cd frontend
npm run dev
```

---

## 2. Docker Containerization Setup

### Backend Dockerfile (`backend/Dockerfile`)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production PostgreSQL Migration
To migrate from SQLite to PostgreSQL, update `DATABASE_URL` in `.env`:
```env
DATABASE_URL=postgresql://rtc_admin:secure_pass@localhost:5432/rtc_university_db
```
SQLAlchemy handles schema migrations seamlessly without altering business logic.
