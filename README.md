# 🎓 RATHINAM TECHNICAL CAMPUS — Late-Event Correction & Reporting System

> **Enterprise Data Quality Dashboard & Stateful Delta Correction Engine**  
> Resolving out-of-order, delayed, and retroactively updated university records with mathematical convergence guarantees.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.0-646C9F?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Tests Passing](https://img.shields.io/badge/Tests-11%2F11%20Passing-brightgreen?style=for-the-badge&logo=pytest)](docs/TESTING.md)
[![Convergence](https://img.shields.io/badge/Ground%20Truth-100%25%20Convergence-success?style=for-the-badge)](docs/EXPERIMENT_REPORT.md)

---

## 📑 Table of Contents

- [Executive Summary](#-executive-summary)
- [The Problem: Historical Report Distortion](#-the-problem-historical-report-distortion)
- [The Solution: Stateful Delta Recalculation](#-the-solution-stateful-delta-recalculation)
- [Mathematical Convergence Guarantee](#-mathematical-convergence-guarantee)
- [Institutional Data Domains](#-institutional-data-domains)
- [System Architecture](#-system-architecture)
- [Key Features](#-key-features)
- [Experimental Benchmarks & Accuracy](#-experimental-benchmarks--accuracy)
- [Tech Stack](#-tech-stack)
- [Project Directory Layout](#-project-directory-layout)
- [Quick Start Guide](#-quick-start-guide)
  - [Prerequisites](#prerequisites)
  - [Backend Setup (FastAPI)](#backend-setup-fastapi)
  - [Frontend Setup (React + Vite)](#frontend-setup-react--vite)
- [REST API Reference](#-rest-api-reference)
- [Testing Suite](#-testing-suite)
- [Documentation Index](#-documentation-index)
- [Ethical Compliance & Synthetic Privacy](#-ethical-compliance--synthetic-privacy)

---

## 🏛️ Executive Summary

The **Rathinam Technical Campus Late-Event Correction & Reporting System** is a production-grade data engineering solution engineered for the **Rathinam Technical Campus Data Administrator / Reporting Manager**. 

University data is inherently asynchronous: attendance slips arrive days late, grades are revised after re-evaluations, lab scores are entered in batches, and placement offers are confirmed weeks after interview drives. Traditional institutional reporting systems take snapshots at midnight and freeze them permanently. When delayed events eventually arrive, either historical reports remain inaccurate, or they overwrite numbers silently with zero accountability.

This platform bridges the gap with a **stateful watermark and delta recalculation engine** that:
- Automatically recalculates historical daily metrics when late events arrive.
- Prevents double-counting and eliminates silent data corruption.
- Dynamically classifies high-impact metric deviations ($\ge 15\%$) into a human-in-the-loop review queue.
- Preserves an immutable append-only audit trail with 1-click compensating rollback capabilities.
- Guarantees **100% mathematical convergence to ground truth**.

---

## ⚠️ The Problem: Historical Report Distortion

Traditional midnight-batch snapshot aggregation fails in real-world academic institutions:

```
Physical Event Occurred (Day D) ───────────────► Ingested on Day D+5 (Delayed Event)
                                                         │
   ┌─────────────────────────────────────────────────────┴─────────────────────────────────────────────────────┐
   ▼                                                                                                           ▼
❌ Naive Snapshot Approach                                                                  ✅ Stateful Delta Engine
- Day D snapshot is frozen at midnight.                                                     - Reopens Day D watermark aggregate.
- Event is credited to Day D+5 or discarded.                                                - Calculates exact delta: Δ = New - Old.
- Historical attendance & marks reports on Day D                                            - Updates Day D aggregate with new version (v1 ➔ v2).
  remain permanently distorted (Baseline MAE > 117.0).                                      - Corrected aggregate matches ground truth (MAE = 0.000).
```

---

## 🎯 The Solution: Stateful Delta Recalculation

Our dual-track engine distinguishes between on-time events ($\le 24\text{ hours}$) and late-arriving events ($> 24\text{ hours}$):

1. **On-Time Events**: Ingested directly into baseline aggregates and establish the initial snapshot ($v_1$).
2. **Late Events**: Processed via the **Correction Engine**, which computes the exact difference ($\Delta = A_{\text{new}} - A_{\text{old}}$), checks impact thresholds, routes high-risk alterations to a review queue, and produces an updated version ($v_2, v_3, \dots$).
3. **Audit Trail**: Every transaction is logged with the actor, event ID, domain, payload, and timestamps.
4. **Compensating Rollback**: Administrators can revert any single correction without deleting history—the system appends a new state record ($v_{k+1}$) with inverse delta values.

---

## 📐 Mathematical Convergence Guarantee

### Naive Baseline Snapshot Aggregate
$$A_{\text{baseline}}(D) = \sum \{ v(e) \mid e \in \text{ValidEvents}, \text{arrival\_date}(e) = D \}$$

### Stateful Corrected Aggregate
$$A_{\text{corrected}}(D, t) = \sum \{ v(e) \mid e \in \text{ValidEvents}, \text{event\_date}(e) = D, \text{ingested\_by}(t) \}$$

### Ground Truth Convergence Invariant
Once all delayed events for a reporting period have arrived and been processed:
$$\text{CorrectedAggregate}(D) \equiv \text{GroundTruth}(D) \quad \forall D$$
$$\text{Corrected MAE} = 0.0000 \quad \text{across all late-arrival scenarios}$$

---

## 📊 Institutional Data Domains

All entities use synthetic data modeled strictly after Rathinam Technical Campus academic workflows:

| Domain | Identifier | Typical Late Event Triggers | Metric Tracked |
| :--- | :--- | :--- | :--- |
| **RTC-Attendance** | `RTC-Attendance` | Biometric sync lag, retroactive medical leaves, on-duty approvals | Daily Present Hours |
| **RTC-Assessment** | `RTC-Assessment` | Grade re-evaluations, deferred lab assessments, manual marks entry | Average Score / Total Marks |
| **RTC-Learning** | `RTC-Learning` | LMS offline sync, asynchronous quiz completions, video logs | Active Hours / Modules Completed |
| **RTC-Placement** | `RTC-Placement` | Delayed company drive confirmations, off-campus interview results | Placed Count / Drive Registrations |

---

## 🏗️ System Architecture

```
                                  [ Institutional Data Sources ]
                         (RTC-Attendance / Assessment / Learning / Placement)
                                                 │
                                                 ▼
                             [ Central Ingestion Gateway (FastAPI) ]
                               (Unique Event ID & Schema Validation)
                                                 │
                        ┌────────────────────────┴────────────────────────┐
                        ▼                                                 ▼
               [ On-Time Event ]                                  [ Late Event (>24h) ]
              (Delay <= 24 Hours)                                  (Delay > 24 Hours)
                        │                                                 │
                        ▼                                                 ▼
              [ Baseline Snapshot ]                              [ Delta Recalculation ]
                 (Version v1)                                     Δ = A_new - A_old
                        │                                                 │
                        │                               ┌─────────────────┴─────────────────┐
                        │                               ▼                                   ▼
                        │                      [ Routine Correction ]             [ High-Impact Alert ]
                        │                       (Impact < 15% Drift)             (Drift >= 15% or Critical)
                        │                               │                                   │
                        │                               ▼                                   ▼
                        │                     [ Auto-Apply (v1 ➔ v2) ]            [ Pending Review Queue ]
                        │                               │                                   │
                        │                               │                         [ Admin Approve / Reject ]
                        │                               │                                   │
                        └───────────────────────┬───────┴───────────────────────────────────┘
                                                ▼
                                   [ Immutable Audit Trail ]
                                      (Append-Only Ledger)
                                                │
                                                ▼
                                  [ Compensating Rollback ]
                                      (Idempotent v_k+1)
                                                │
                                                ▼
                                [ Vite + React Executive UI ]
```

---

## ✨ Key Features

- **⚡ Stateful Watermark & Delta Recalculation**: Recomputes historical reporting dates on the fly without full-database rescans.
- **🛡️ Idempotent Ingestion**: Rejects duplicate event IDs at the database constraint level while maintaining an audit log of rejected duplicates.
- **⚖️ Side-by-Side Baseline vs. Corrected Diff**: Live visual comparisons illustrating baseline error vs. corrected accuracy.
- **🚨 High-Impact Review Queue**: Automated isolation of corrections causing $\ge 15\%$ drift or altering high-stakes placement/graduation outcomes.
- **📜 Immutable Audit Trail**: Cryptographically traceable ledger recording event arrival timestamps, user actors, and payload diffs.
- **🔄 Compensating Rollback Engine**: 1-click idempotent reversal that creates an append-only compensating version rather than destructive row deletion.
- **🧪 Deterministic 8-Step Interactive Demo**: Built-in guided simulation walking through late arrivals, duplicate rejection, review escalation, approval, and rollback.
- **📈 Reproducible Benchmark Suite**: Built-in experimental framework measuring MAE and RMSE across 6 real-world scenarios.

---

## 🔬 Experimental Benchmarks & Accuracy

Empirical evaluation executed across 6 institutional stress scenarios (Random Seed: 42):

| Scenario | Late Ratio | Total Events | Baseline MAE | Corrected MAE | Exact Match % | Convergence |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Scenario 1: 0% Late Events** | 0% | 200 | 53.365 | **0.000** | **100.0%** | ✅ Verified |
| **Scenario 2: 5% Late Events** | 5% | 200 | 55.360 | **0.000** | **100.0%** | ✅ Verified |
| **Scenario 3: 10% Late Events** | 10% | 200 | 58.420 | **0.000** | **100.0%** | ✅ Verified |
| **Scenario 4: 25% Late Events** | 25% | 200 | 100.035 | **0.000** | **100.0%** | ✅ Verified |
| **Scenario 5: 15% Late + Duplicates** | 15% | 200 | 70.480 | **0.000** | **100.0%** | ✅ Verified |
| **Scenario 6: 30% Late (7-Day Lag)** | 30% | 200 | 117.250 | **0.000** | **100.0%** | ✅ Verified |

*Full evaluation methodology and logs are available in [`docs/EXPERIMENT_REPORT.md`](docs/EXPERIMENT_REPORT.md).*

---

## 💻 Tech Stack

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
- **Server**: [Uvicorn](https://www.uvicorn.org/) ASGI Server
- **ORM & Database**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) with SQLite (zero-config, PostgreSQL-ready)
- **Data Validation**: [Pydantic v2](https://docs.pydantic.dev/)
- **Test Suite**: [pytest](https://docs.pytest.org/)

### Frontend
- **Framework**: [React 18](https://react.dev/) + [Vite](https://vitejs.dev/)
- **Styling**: [Tailwind CSS 3.4](https://tailwindcss.com/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **Charts & Visualization**: [Recharts](https://recharts.org/)
- **HTTP Client**: Native Fetch with reactive state

---

## 📁 Project Directory Layout

```
UNIVERSITY_DATA/
├── backend/
│   ├── app/
│   │   ├── audit.py             # Compensating rollback & audit trail logic
│   │   ├── config.py            # System configuration & thresholds
│   │   ├── correction.py        # Delta recalculation & review workflow
│   │   ├── database.py          # SQLAlchemy session & SQLite engine
│   │   ├── demo.py              # 8-step controlled demonstration scenario
│   │   ├── experiments.py       # Empirical benchmark runner
│   │   ├── generator.py         # Synthetic institutional event generator
│   │   ├── main.py              # FastAPI application & route declarations
│   │   ├── models.py            # Database schemas (Events, Reports, Audit)
│   │   ├── pipeline.py          # Event ingestion & deduplication pipeline
│   │   ├── schemas.py           # Pydantic request & response models
│   │   └── seed.py              # Initial database seed script
│   ├── tests/
│   │   ├── test_audit_rollback.py
│   │   ├── test_correction.py
│   │   ├── test_integration.py
│   │   ├── test_pipeline.py
│   │   └── test_reconciliation.py
│   ├── generate_reconciliation_report.py
│   ├── run_experiments.py
│   └── requirements.txt
├── data/
│   └── results/
│       ├── experiment_summary.json
│       └── reconciliation_report.json
├── docs/
│   ├── ARCHITECTURE.md          # Technical architecture & timestamp semantics
│   ├── DEPLOYMENT.md            # Docker containerization & production setup
│   ├── ETHICS_NOTE.md           # Synthetic data privacy guarantees
│   ├── EXPERIMENT_REPORT.md     # Detailed benchmark data across 6 scenarios
│   ├── FINAL_DEMO.md            # Interactive walkthrough guide
│   ├── METHODOLOGY.md           # Mathematical models & delta formulations
│   ├── STAKEHOLDER_WALKTHROUGH.md # 7 core stakeholder question answers
│   ├── STUDENT_PROJECT_PHASE_REPORT.md # Academic Capstone / Phase-I submission report
│   └── TESTING.md               # Unit and integration test specifications
├── frontend/
│   ├── src/
│   │   ├── api/                 # API client services
│   │   ├── components/          # React components (Dashboard, Audit, Demo)
│   │   ├── App.jsx              # Main dashboard application
│   │   ├── main.jsx             # React DOM root
│   │   └── index.css            # Tailwind CSS directives
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python**: Version 3.10 or higher (`python --version` or `py --version`)
- **Node.js**: Version 18 or higher (`node --version`)
- **npm**: Version 9 or higher (`npm --version`)

---

### Backend Setup (FastAPI)

1. **Navigate to backend folder**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment** *(optional but recommended)*:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the test suite (11/11 tests)**:
   ```bash
   pytest -v
   ```

5. **Run the experiment benchmarks**:
   ```bash
   python run_experiments.py
   ```

6. **Start the backend development server**:
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```
   *The interactive API documentation is available at: `http://localhost:8000/docs`*

---

### Frontend Setup (React + Vite)

1. **Open a new terminal and navigate to frontend folder**:
   ```bash
   cd frontend
   ```

2. **Install frontend dependencies**:
   ```bash
   npm install
   ```

3. **Start the Vite development server**:
   ```bash
   npm run dev
   ```

4. **Access the Dashboard**:
   Open your browser and navigate to:
   ```
   http://localhost:3000
   ```

---

## 🔌 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | System health check and institutional metadata |
| `GET` | `/api/metrics/summary` | Executive summary (total events, late count, drift, audit size) |
| `POST` | `/api/events/ingest` | Ingest an event with idempotency and lateness evaluation |
| `GET` | `/api/reports/daily` | Fetch daily reports across all domains with baseline vs. corrected |
| `GET` | `/api/reports/{id}/versions` | Retrieve version history for a specific report ($v_1 \to v_k$) |
| `GET` | `/api/corrections/pending` | Fetch pending high-impact corrections requiring review |
| `POST` | `/api/corrections/{id}/review` | Approve or reject a high-impact pending correction |
| `POST` | `/api/corrections/{id}/rollback` | Perform a compensating rollback on an applied correction |
| `GET` | `/api/audit/logs` | Query the immutable audit trail with filtering |
| `POST` | `/api/demo/run-step` | Execute a step in the controlled 8-step interactive demo |
| `POST` | `/api/experiments/run` | Execute the full 6-scenario benchmark suite |

---

## 🧪 Testing Suite

The repository includes a comprehensive automated test suite covering unit tests, idempotency checks, mathematical reconciliation, and end-to-end user flows:

```bash
cd backend
pytest -v
```

### Test Coverage Highlights
- `test_pipeline.py`: Tests on-time ingestion, late event detection, unique event ID deduplication, and invalid payload rejection.
- `test_correction.py`: Tests baseline aggregation, delta calculation, and high-impact ($\ge 15\%$) threshold escalation.
- `test_audit_rollback.py`: Tests append-only audit trail logging and compensating rollback idempotency.
- `test_reconciliation.py`: Proves the Ground Truth Convergence Invariant ($A_{\text{corrected}} \equiv A_{\text{GT}}$) across all dates.
- `test_integration.py`: Validates the complete flow from ingestion through review, approval, and UI synchronization.

---

## 📚 Documentation Index

For deep-dive technical insights, consult the comprehensive documentation in [`docs/`](docs/):

- 🏛️ [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): Database schemas, timestamp semantics, and latency definitions.
- 📐 [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md): Mathematical formulations for drift, impact scores, and watermark delta logic.
- 🧪 [`docs/TESTING.md`](docs/TESTING.md): Comprehensive test specifications and assertions.
- 📈 [`docs/EXPERIMENT_REPORT.md`](docs/EXPERIMENT_REPORT.md): Measured benchmark outputs across all 6 stress scenarios.
- 🚀 [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md): Containerization (Docker) and PostgreSQL production deployment.
- 👥 [`docs/STAKEHOLDER_WALKTHROUGH.md`](docs/STAKEHOLDER_WALKTHROUGH.md): Direct answers to the 7 core operational questions.
- 🔒 [`docs/ETHICS_NOTE.md`](docs/ETHICS_NOTE.md): Ethical data governance and synthetic privacy guarantees.
- 🎬 [`docs/FINAL_DEMO.md`](docs/FINAL_DEMO.md): Evaluation walkthrough script for live presentation.
- 📘 [`docs/STUDENT_PROJECT_PHASE_REPORT.md`](docs/STUDENT_PROJECT_PHASE_REPORT.md): **Academic Capstone / Phase-I Project Evaluation Report** (Anna University & RTC format).

---

## 🔒 Ethical Compliance & Synthetic Privacy

All records, student IDs (`RTC-STU-0001` through `RTC-STU-1000`), marks, attendance, and placement statistics generated and used within this repository are **100% synthetic demonstration data**. 
- No actual student Personally Identifiable Information (PII) is included or stored.
- Data distributions are calibrated for academic evaluation while respecting zero-PII privacy standards.
- Designed in accordance with educational data protection best practices.

---

## 👨‍💻 Maintainer & Attribution

- **Institution**: Rathinam Technical Campus
- **Project Repository**: [https://github.com/nishams63/university_data](https://github.com/nishams63/university_data)
- **Primary Stakeholder Focus**: Data Administrator / Institutional Reporting Manager
- **License**: Educational & Institutional Demonstration Use
