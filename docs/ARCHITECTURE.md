# SYSTEM ARCHITECTURE & DISTRIBUTED DESIGN SPECIFICATION

**Institution:** Rathinam Technical Campus (Autonomous), Coimbatore  
**Project:** Late-Event Correction & Daily Reporting System: A Stateful Watermark and Delta Recalculation Engine for Institutional Big Data  
**Milestone:** 70% Engineering Review  
**Author:** RTC Institutional Data Engineering Group  

---

## 1. System Overview & Core Objectives

Institutional data pipelines at Rathinam Technical Campus ingest continuous streams across four operational domains:
1. `RTC-Attendance`: Automated turnstile and RFID classroom check-ins.
2. `RTC-Assessment`: Mid-term exams, lab assessments, and semester score evaluations.
3. `RTC-Learning`: Digital LMS course module completions and quiz submissions.
4. `RTC-Placement`: Corporate campus drive registrations, interviews, and final placement offers.

In traditional university management information systems (MIS), late-arriving events (caused by network downtime, edge turnstile batch synchronization, or delayed instructor entry) either corrupt current-day aggregates or are silently dropped. 

This architecture implements a **Stateful Watermark and Delta Recalculation Engine** that decouples event arrival time from historical event occurrence time, atomically updating affected historical reports while preserving an immutable, auditable version lineage.

---

## 2. High-Level Architectural Diagram

```
+---------------------------------------------------------------------------------------------------+
|                                 RATHINAM TECHNICAL CAMPUS DATA SOURCES                             |
|    [Turnstile Edge]           [LMS Online Portal]         [Exam Portal]       [Placement Desk]    |
+-----------+----------------------------+-----------------------+---------------------+------------+
            |                            |                       |                     |
            +----------------------------v-----------------------v---------------------+
                                         | Ingestion Stream (JSON Events)
                                         v
+---------------------------------------------------------------------------------------------------+
|                                     INGESTION & VALIDATION GATEWAY                                |
|  - Idempotency & Duplicate Rejection: Event ID PK Hash Check                                     |
|  - Domain-Specific Payload Validation: Schema conformance, score bounds, status verification      |
|  - Temporal Decoupling: Event Timestamp (t_E) vs Arrival Timestamp (t_A)                          |
+----------------------------------------+----------------------------------------------------------+
                                         |
                                         v
+---------------------------------------------------------------------------------------------------+
|                                STATEFUL WATERMARK & DELTA ENGINE                                  |
|  - Watermark Evaluation: Delay = (t_A - t_E). If Delay > 24h -> Flag LATE                        |
|  - O(1) Contribution Extraction: delta = f(domain, payload)                                       |
|  - Impact Threshold Gate: Relative Drift = |delta| / max(|old_agg|, 1) * 100                     |
|    * If Drift >= 15% OR Outcome Risk -> Route to Human Review Queue (PENDING_REVIEW)              |
|    * If Drift < 15% AND Routine -> Apply Immediately (AUTO_CORRECTED)                            |
+----------------------------------------+----------------------------------------------------------+
                                         |
                                         v
+---------------------------------------------------------------------------------------------------+
|                         ATOMIC TRANSACTION & MONOTONIC VERSION LEDGER                             |
|  - Single Session Transaction Boundary: [RawEvent + DailyReport + ReportVersion + AuditLog]       |
|  - Monotonic Versioning: Current Version v_n -> v_{n+1} (No in-place aggregate mutation)         |
|  - SQLite Write-Ahead Logging (WAL): Non-blocking readers, 10s busy timeout, foreign keys ON       |
+----------------------------------------+----------------------------------------------------------+
                                         |
                                         v
+---------------------------------------------------------------------------------------------------+
|                                PRESENTATION & AUDIT EXPLORER (VITE REACT)                         |
|  - Dashboard Status & Key Indicators                                                             |
|  - Version Lineage Timeline (v1 -> v2 -> v3) with Diff Visualizer                                |
|  - Human-in-the-Loop Administrator Approval Queue with Confirmations                             |
|  - Performance & PRAGMA Diagnostic Explorer                                                      |
+---------------------------------------------------------------------------------------------------+
```

---

## 3. Timestamp Semantics & Stateful Watermark Model

To prevent temporal distortion, every ingested tuple enforces four separate time attributes:
1. **$t_E$ (`event_timestamp`):** The physical occurrence timestamp (e.g., lecture attendance at `2026-08-20 09:00:00`). The institutional reporting date $D$ is derived strictly as $D = \text{date}(t_E)$.
2. **$t_A$ (`arrival_timestamp`):** The wall-clock timestamp when the central gateway receives the record.
3. **$t_P$ (`processing_timestamp`):** The timestamp when the atomic transaction was committed.
4. **$t_W$ (Watermark Timestamp):** The dynamic watermark defined as:
   $$t_W = \max(t_E) - \Delta_{\text{threshold}}$$
   Where $\Delta_{\text{threshold}} = 24.0 \text{ hours}$.

### Lateness Rule
$$\text{delay\_hours} = \frac{t_A - t_E}{3600}$$
- If $\text{delay\_hours} \le 24.0$: Event is **ON-TIME**. Contributes to the day's baseline snapshot.
- If $\text{delay\_hours} > 24.0$: Event is **LATE**. Triggers historical report delta recalculation for date $D$.

---

## 4. Delta Recalculation Algorithm: $O(1)$ Incremental State Math

### Problem with Naive Aggregation
In early prototypes, when a late event arrived, systems re-scanned the entire raw events table for date $D$ ($O(N)$ table scan), parsed every JSON payload, and recalculated the sum from scratch. Under a workload of 5,000 events, this induced $O(N^2)$ algorithmic complexity ($\approx 37.5 \text{ million}$ record reads).

### Engineered $O(1)$ Stateful Delta Math
The system computes the incremental delta $\delta_i$ directly from the event payload:
$$\delta_i = \text{extract\_event\_metric\_contribution}(\text{domain}, \text{payload})$$
$$\text{Aggregate}_{v+1}(D) = \text{Aggregate}_v(D) + \delta_i$$

- **Domain Contributions:**
  - `RTC-Attendance`: $+1.0$ for `Present` or `Late_Leave`, $+0.0$ for `Absent`.
  - `RTC-Assessment`: $+\text{score}$ (points).
  - `RTC-Learning`: $+\text{quiz\_score}$ (points).
  - `RTC-Placement`: $+1.0$ if `offer_status == "Selected"`, $+0.0$ otherwise.

Independent ground truth calculation (`compute_ground_truth(db, date, domain)`) is preserved strictly for:
1. Periodic asynchronous reconciliation audits.
2. Verification when an administrator approves a high-impact review.

---

## 5. Mathematical Invariant Proof

### Core Invariant
Let $E(D)$ be the complete set of all valid, non-duplicate events occurring on date $D$, regardless of whether they arrive on time ($E_{\text{on-time}}(D)$) or late ($E_{\text{late}}(D)$):
$$E(D) = E_{\text{on-time}}(D) \cup E_{\text{late}}(D)$$

The Ground Truth aggregate is defined by independent full evaluation:
$$\text{GroundTruth}(D) = \sum_{e \in E(D)} \text{contribution}(e)$$

The incrementally corrected aggregate is:
$$\text{CorrectedAggregate}(D) = \text{Baseline}(D) + \sum_{e_L \in E_{\text{late}}(D)} \delta(e_L)$$
Since $\text{Baseline}(D) = \sum_{e \in E_{\text{on-time}}(D)} \text{contribution}(e)$ and $\delta(e_L) \equiv \text{contribution}(e_L)$:
$$\text{CorrectedAggregate}(D) \equiv \text{GroundTruth}(D)$$
$$\text{Mean Absolute Error (MAE)} \equiv 0.0000$$

This invariant was verified across all 6 experimental scenarios with 100.0% exact match.

---

## 6. Distributed Scaling & Architecture Extension Roadmap

While SQLite with WAL mode delivers high performance for single-campus deployments (<1 MB RAM, 163 eps), the architecture is designed to scale horizontally:

| Component | 70% Engineering Prototype (Current) | Future Distributed Production (Phase 3 Horizon) |
| :--- | :--- | :--- |
| **Ingestion Queue** | FastAPI in-memory / synchronous atomic endpoint | Distributed Apache Kafka / RabbitMQ partitioned by `(domain, reporting_date)` |
| **Storage Engine** | SQLite 3 (WAL mode, busy timeout 10s, FKs ON) | PostgreSQL with TimescaleDB hypertables or ClickHouse column storage |
| **Watermark State** | In-database sliding watermark window | Apache Flink stateful tumbling/sliding event-time window |
| **Versioning** | Relational `report_versions` table with cascade | Apache Iceberg / Delta Lake temporal version travel |
| **Review Workflow**| Relational human review queue with optimistic locks | Camunda / Temporal workflow engine with institutional role-based RBAC |
