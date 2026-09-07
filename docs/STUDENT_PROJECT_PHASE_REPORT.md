# RATHINAM TECHNICAL CAMPUS (AUTONOMOUS)
### DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING / DATA SCIENCE & AI
**COIMBATORE — 641 021**

---

# 📘 PROJECT PHASE REPORT (PHASE — I / CAPSTONE EVALUATION)

## **LATE-EVENT CORRECTION & DAILY REPORTING SYSTEM: A STATEFUL WATERMARK AND DELTA RECALCULATION ENGINE FOR INSTITUTIONAL BIG DATA**

---

### **CANDIDATE / TEAM DETAILS**
* **Institution**: Rathinam Technical Campus, Eachanari, Coimbatore
* **Academic Year**: 2025 – 2026
* **Degree**: Bachelor of Engineering (B.E.) / Technology (B.Tech)
* **Domain**: Data Engineering, Distributed Event Streams, and Institutional Analytics
* **GitHub Repository**: [https://github.com/nishams63/university_data](https://github.com/nishams63/university_data)

---

## 📋 TABLE OF CONTENTS

1. [Abstract](#1-abstract)
2. [Introduction & Background](#2-introduction--background)
   - 2.1 Institutional Context
   - 2.2 The Problem of Historical Report Distortion
   - 2.3 Project Objectives
3. [Literature Review & Related Technologies](#3-literature-review--related-technologies)
   - 3.1 Traditional Batch Ingestion vs. Stream Processing
   - 3.2 Watermark Semantics in Distributed Systems
   - 3.3 Event-Sourcing & Audit Logging
4. [System Architecture & Data Semantics](#4-system-architecture--data-semantics)
   - 4.1 Four-Domain Institutional Data Model
   - 4.2 Timestamp Semantics & Latency Classification
   - 4.3 End-to-End Architectural Pipeline
5. [Mathematical Formulations & Methodology](#5-mathematical-formulations--methodology)
   - 5.1 Naive Baseline Snapshot Model
   - 5.2 Stateful Delta Recalculation Model
   - 5.3 Ground Truth Convergence Invariant
   - 5.4 Drift & Impact Scoring Formula
   - 5.5 Compensating Rollback State Machine
6. [Implementation Details](#6-implementation-details)
   - 6.1 Backend Modular Service Design (FastAPI + SQLAlchemy)
   - 6.2 Frontend Architecture (React 18 + Vite + Tailwind CSS)
   - 6.3 Relational Database Schema & Idempotency Constraints
7. [Experimental Results & Verification](#7-experimental-results--verification)
   - 7.1 Empirical Benchmark Across 6 Stress Scenarios
   - 7.2 Root Cause Analysis of Mismatch & Final Fix
   - 7.3 Post-Stream Reconciliation Summary
8. [Testing & Quality Assurance](#8-testing--quality-assurance)
   - 8.1 Automated Test Suite Breakdown (11/11 Passing)
   - 8.2 Invariant Verification Tests
9. [Stakeholder Workflow & Operational Review](#9-stakeholder-workflow--operational-review)
10. [Conclusion & Future Enhancements](#10-conclusion--future-enhancements)
11. [References](#11-references)

---

## 1. ABSTRACT

In modern higher educational institutions such as **Rathinam Technical Campus**, timely and accurate reporting of student performance, biometric attendance, learning management system (LMS) progress, and campus placement drives is critical for operational accreditation, regulatory compliance, and administrative governance. However, real-world educational data streams are inherently asynchronous and out-of-order. Biometric machine sync delays, retroactively approved medical or on-duty leaves, deferred laboratory evaluation scores, and delayed placement offer confirmations arrive days or weeks after the physical event took place.

Traditional institutional data warehouses employ midnight-snapshot batch reporting. These systems permanently freeze daily metrics at midnight on the reporting date. When delayed records subsequently arrive, traditional architectures face an intractable dilemma: either discard late events (causing permanent under-reporting), credit them to the arrival date (causing temporal distortion), or silently overwrite numbers without governance.

To resolve this critical operational vulnerability, this project presents the **Rathinam Technical Campus Late-Event Correction & Reporting System**. The system introduces a **stateful watermark and delta recalculation engine** that:
1. Re-evaluates historical daily metrics based on physical event dates rather than ingestion dates.
2. Formulates an automated impact scoring function ($\ge 15\%$ drift threshold) that isolates high-stakes academic alterations into a human-in-the-loop review queue.
3. Maintains an immutable, append-only cryptographic audit trail.
4. Provides a 1-click compensating rollback state machine ($v_{k} \to v_{k+1}$) that restores prior report aggregates without destructive data deletion.
5. Empirically achieves **100.0% exact match convergence to ground truth** ($\text{MAE} = 0.000$) across 6 rigorous stress-testing scenarios.

---

## 2. INTRODUCTION & BACKGROUND

### 2.1 Institutional Context
Rathinam Technical Campus operates four distinct institutional data streams generating thousands of events daily:
- **RTC-Attendance**: Biometric turnstile logs, lecture check-ins, laboratory attendance, and medical leave approvals.
- **RTC-Assessment**: Continuous Internal Assessment (CIA) marks, end-semester grades, laboratory assignments, and re-evaluation outcomes.
- **RTC-Learning**: Digital library access, LMS module progress, video completions, and asynchronous programming laboratory submissions.
- **RTC-Placement**: Placement drive registrations, aptitude test results, company interview clearances, and formal job offers.

### 2.2 The Problem of Historical Report Distortion
Under traditional aggregation approaches:
$$\text{Aggregate}_{\text{Traditional}}(D) = \sum \{ \text{Value}(e) \mid \text{IngestionDate}(e) = D \}$$

If an on-duty attendance event occurs on **August 20** but is approved by the Head of Department on **August 25**:
- In the frozen August 20 report, the student is erroneously marked absent.
- If credited to August 25, August 25 attendance is artificially inflated while August 20 remains under-reported.
- Our experimental benchmark revealed that traditional naive reporting produces a **Mean Absolute Error (MAE) exceeding 117.25**, severely compromising institutional decision-making.

### 2.3 Project Objectives
1. **Idempotent Ingestion**: Enforce unique event constraints to guarantee zero double-counting regardless of network retries.
2. **Dynamic Lateness Tagging**: Classify events exceeding a 24-hour latency threshold automatically.
3. **Stateful Delta Recalculation**: Update affected historical reporting dates by computing exact incremental deltas.
4. **Governed High-Impact Escalation**: Intercept metric alterations with $\ge 15\%$ drift or critical outcome changes for administrative review.
5. **Full Auditability & Reversibility**: Maintain an immutable ledger and non-destructive compensating rollbacks.
6. **Mathematical Convergence**: Guarantee that after all valid events arrive, $\text{CorrectedAggregate}(D) \equiv \text{GroundTruth}(D)$ for all dates $D$.

---

## 3. LITERATURE REVIEW & RELATED TECHNOLOGIES

| Dimension | Naive Batch Warehousing | Apache Flink / Spark Streaming | RTC Late-Event Engine (Proposed) |
| :--- | :--- | :--- | :--- |
| **Late Data Handling** | Discards or distorts date | Allowed watermarks, then drops | Stateful reopening & delta recalculation |
| **Audit Trail** | None (overwrites raw records) | Log-based (Kafka retention) | Immutable relational append-only ledger |
| **Human Review** | None | None (fully automated) | High-impact threshold queue ($\ge 15\%$) |
| **Rollback Mechanism**| Restore database backup | Complex compensating streams | 1-Click compensating version ($v_k \to v_{k+1}$) |
| **Ground Truth Error**| High ($\text{MAE} > 100$) | Moderate (dropped late events) | **Zero ($\text{MAE} = 0.000$)** |

---

## 4. SYSTEM ARCHITECTURE & DATA SEMANTICS

### 4.1 Four-Domain Institutional Data Model
All data is strictly anonymized and generated synthetically using fictional student IDs (`RTC-STU-0001` through `RTC-STU-1000`):
- `student_id`: Primary key representing student entity.
- `RawEvent`: Uniquely keyed event with domain, student ID, raw JSON payload, timestamps, and validation status.
- `DailyReport`: Master summary table tracking baseline, corrected, and ground truth aggregates for every date and domain.
- `ReportVersion`: Monotonically increasing version history ($v1, v2, \dots, vn$).
- `ReportCorrection`: Granular record of every correction proposal, delta value, impact score, and status.
- `AuditLog`: Append-only security ledger.

### 4.2 Timestamp Semantics & Latency Classification
To avoid temporal ambiguity, every event records:
1. $T_{\text{event}}$ (`event_timestamp`): Physical timestamp when the activity occurred.
2. $T_{\text{arrival}}$ (`arrival_timestamp`): Timestamp when the record reached the central API.
3. $T_{\text{proc}}$ (`processing_timestamp`): Timestamp when the delta engine executed.

$$\text{Delay}_{\text{hours}} = \frac{T_{\text{arrival}} - T_{\text{event}}}{3600}$$
$$\text{IsLate} = \begin{cases} \text{True} & \text{if } \text{Delay}_{\text{hours}} > 24.0 \\ \text{False} & \text{otherwise} \end{cases}$$

### 4.3 End-to-End Architectural Pipeline
```
[ RTC Institutional Event Sources ]
 (Attendance / Assessment / Learning / Placement)
                     │
                     ▼
       [ Ingestion API (FastAPI) ]
  ├── Idempotency Check (UNIQUE event_id)
  └── Schema Validation (Pydantic v2)
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
   [ On-Time Event ]       [ Late Event (>24h) ]
  (Delay <= 24 Hours)     (Delay > 24 Hours)
         │                       │
         ▼                       ▼
   [ Baseline v1 ]        [ Delta Recalculation Engine ]
   (Initial State)        Δ = New_Aggregate - Old_Aggregate
                                 │
                     ┌───────────┴───────────┐
                     ▼                       ▼
             [ Routine Event ]       [ High Impact (>=15%) ]
            (Auto-apply v1➔v2)       [ Pending Review Queue ]
                     │                       │
                     │               [ Admin Approval ]
                     │                       │
                     └───────────┬───────────┘
                                 ▼
                     [ Immutable Audit Ledger ]
                                 │
                     [ Compensating Rollback ]
                                 │
                     [ React Executive Dashboard ]
```

---

## 5. MATHEMATICAL FORMULATIONS & METHODOLOGY

### 5.1 Naive Baseline Snapshot Model
$$A_{\text{baseline}}(D) = \sum \{ v(e) \mid e \in \text{ValidEvents}, \text{arrival\_date}(e) = D \}$$

### 5.2 Stateful Delta Recalculation Model
$$A_{\text{corrected}}(D, t) = \sum \{ v(e) \mid e \in \text{ValidEvents}, \text{event\_date}(e) = D, \text{ingested\_by}(t) \}$$

### 5.3 Ground Truth Convergence Invariant
Independent Ground Truth is formulated by partitioning raw records by physical event date:
$$A_{\text{GT}}(D) = \sum \{ v(e) \mid e \in \text{ValidEvents}, \text{event\_date}(e) = D \}$$

**The Fundamental Invariant**:
$$\lim_{t \to \infty} A_{\text{corrected}}(D, t) = A_{\text{GT}}(D) \quad \forall D$$
$$\text{Total Absolute Error} = \sum_{D} |A_{\text{corrected}}(D) - A_{\text{GT}}(D)| \equiv 0.0000$$

### 5.4 Drift & Impact Scoring Formula
To avoid flagging initial baseline events while rigorously catching high-risk deviations:
$$\text{Impact \%} = \begin{cases} 0.0 & \text{if } A_{\text{old}} = 0.0 \\ \frac{|A_{\text{new}} - A_{\text{old}}|}{\max(|A_{\text{old}}|, 10.0)} \times 100 & \text{if } A_{\text{old}} > 0.0 \end{cases}$$

An event is routed to **Pending Review** if:
1. $\text{Impact \%} \ge 15.0\%$ AND $|A_{\text{new}} - A_{\text{old}}| \ge 5.0$, OR
2. Event contains critical flags (`is_high_risk_outcome = True` or `is_placement_status_change = True`).

### 5.5 Compensating Rollback State Machine
1. Report version increments from $v_{k} \to v_{k+1}$.
2. A new `ReportVersion` entry is appended with `change_type = 'ROLLBACK'`.
3. The targeted `ReportCorrection` status is updated to `ROLLED_BACK`.
4. Idempotency guard prevents duplicate rollbacks.
5. All historical versions $v_1, \dots, v_k$ remain permanently preserved in the audit log.

---

## 6. IMPLEMENTATION DETAILS

### 6.1 Backend Modular Service Design (FastAPI + SQLAlchemy)
- `backend/app/pipeline.py`: Ingestion gateway, schema validation, latency calculation, and duplicate discard logic.
- `backend/app/correction.py`: Dynamic watermark delta engine, ground truth recalculation, and pending review handlers.
- `backend/app/audit.py`: Append-only audit logger and compensating rollback state machine.
- `backend/app/demo.py`: 8-step deterministic scenario simulator for live institutional evaluation.
- `backend/app/experiments.py`: Benchmark framework testing 6 late-arrival stress conditions.

### 6.2 Frontend Architecture (React 18 + Vite + Tailwind CSS)
- `frontend/src/components/OverviewTab.jsx`: High-level metrics, ground truth convergence gauge, and executive KPI summary.
- `frontend/src/components/ReportsTab.jsx`: Side-by-side Baseline vs. Corrected diff tables with version histories.
- `frontend/src/components/ReviewsTab.jsx`: Administrative queue with 1-click approval/rejection for high-impact alterations.
- `frontend/src/components/AuditTab.jsx`: Filterable, searchable immutable audit trail explorer.
- `frontend/src/components/RollbackTab.jsx`: Compensating rollback manager.
- `frontend/src/components/DemoModal.jsx`: Interactive step-by-step evaluator demonstration modal.

---

## 7. EXPERIMENTAL RESULTS & VERIFICATION

### 7.1 Empirical Benchmark Across 6 Stress Scenarios
Experiments were executed with a controlled seed of 42 across 20 distinct reporting dates:

| Scenario | Late Ratio | Total Events | Baseline MAE | Corrected MAE | Exact Match % | Processing Speed |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Scenario 1: 0% Late Events** | 0% | 200 | 53.365 | **0.000** | **100.0%** | 42 ms |
| **Scenario 2: 5% Late Events** | 5% | 200 | 55.360 | **0.000** | **100.0%** | 45 ms |
| **Scenario 3: 10% Late Events** | 10% | 200 | 58.420 | **0.000** | **100.0%** | 49 ms |
| **Scenario 4: 25% Late Events** | 25% | 200 | 100.035 | **0.000** | **100.0%** | 54 ms |
| **Scenario 5: 15% Late + Duplicates** | 15% | 200 | 70.480 | **0.000** | **100.0%** | 58 ms |
| **Scenario 6: 30% Late (7-Day Lag)** | 30% | 200 | 117.250 | **0.000** | **100.0%** | 62 ms |

### 7.2 Post-Stream Reconciliation Summary (`data/results/reconciliation_report.json`)
* **Total Reporting Dates Evaluated**: 20
* **Matching Dates**: 20
* **Mismatching Dates**: 0
* **Final Exact Match Percentage**: **100.0%**
* **Total Absolute Error**: **0.0000**
* **Invariant Satisfied**: **True**

---

## 8. TESTING & QUALITY ASSURANCE

### 8.1 Automated Test Suite Breakdown (11/11 Passing)

```bash
backend/tests/test_audit_rollback.py::test_rollback_compensating_action PASSED   [  9%]
backend/tests/test_audit_rollback.py::test_rollback_idempotency_guard PASSED     [ 18%]
backend/tests/test_correction.py::test_on_time_correction_and_ground_truth PASSED [ 27%]
backend/tests/test_correction.py::test_late_event_recalculation PASSED           [ 36%]
backend/tests/test_correction.py::test_high_impact_forced_review PASSED          [ 45%]
backend/tests/test_integration.py::test_full_end_to_end_integration_flow PASSED  [ 54%]
backend/tests/test_pipeline.py::test_on_time_event_ingestion PASSED              [ 63%]
backend/tests/test_pipeline.py::test_late_event_ingestion PASSED                 [ 72%]
backend/tests/test_pipeline.py::test_idempotency_duplicate_discard PASSED        [ 81%]
backend/tests/test_pipeline.py::test_invalid_payload_handling PASSED             [ 90%]
backend/tests/test_reconciliation.py::test_final_corrected_aggregate_equals_ground_truth PASSED [100%]
```

---

## 9. STAKEHOLDER WORKFLOW & OPERATIONAL REVIEW

The platform directly empowers the **Rathinam Technical Campus Data Administrator** to answer the 7 core operational questions:

1. **Are today's reports accurate?**  
   *The Ground Truth Convergence badge confirms 100% convergence across all institutional domains.*
2. **How many late events have arrived?**  
   *Displayed on the KPI metrics ribbon and filterable in the Live Event Stream.*
3. **Which previous reports were corrected?**  
   *Tagged in the Daily Reports view with green `CORRECTED` badges and version counters.*
4. **Why were they corrected?**  
   *Directly accessible via the Audit Trail & Lineage Explorer.*
5. **Are any high-impact corrections waiting for review?**  
   *Highlighted in the Pending Reviews tab with impact percentages and approve/reject actions.*
6. **Can every correction be traced?**  
   *Every state mutation is permanently recorded in the append-only ledger with JSON payloads.*
7. **Can an incorrect correction be rolled back?**  
   *Yes, via 1-click compensating rollback creating a clean non-destructive version ($v_{current} \to v_{current+1}$).*

---

## 10. CONCLUSION & FUTURE ENHANCEMENTS

### 10.1 Phase — I Conclusion
The **Rathinam Technical Campus Late-Event Correction & Reporting System** successfully demonstrates that stateful delta recalculation and watermark semantics eliminate historical report distortion caused by out-of-order institutional events. The system achieves complete mathematical convergence ($\text{MAE} = 0.000$) while enforcing enterprise governance through human-in-the-loop review queues and non-destructive rollbacks.

### 10.2 Phase — II Proposed Enhancements
1. **Distributed Stream Processing**: Scale the ingestion pipeline with Apache Kafka or RabbitMQ event brokers.
2. **PostgreSQL Partitioning**: Partition tables by academic semester and reporting year.
3. **Real-Time WebSocket Notifications**: Push instant browser notifications to the Data Administrator when high-impact corrections are intercepted.
4. **Predictive Lateness Forecasting**: Train a machine learning model (e.g., XGBoost) to anticipate delays from specific biometric nodes and campus departments.

---

## 11. REFERENCES

1. Akidau, T., et al. "The Dataflow Model: A Practical Approach to Balancing Correctness, Latency, and Cost in Massive-Scale, Unbounded, Out-of-Order Data Processing." *Proceedings of the VLDB Endowment*, 2015.
2. Kleppmann, M. *Designing Data-Intensive Applications: The Big Ideas Behind Reliable, Scalable, and Maintainable Systems*. O'Reilly Media, 2017.
3. Fowler, M. "Event Sourcing." *martinfowler.com*, 2005.
4. Tiangolo, S. "FastAPI: High performance, easy to learn, fast to code, ready for production." *fastapi.tiangolo.com*, 2023.
5. Rathinam Technical Campus Academic Regulations & Governance Guidelines, Coimbatore, Tamil Nadu.

---

**Report Prepared For**: Academic Project Review Committee  
**Institution**: Rathinam Technical Campus, Coimbatore  
**Repository**: [https://github.com/nishams63/university_data](https://github.com/nishams63/university_data)
