# Review 3 Evidence Package & Screenshot Catalog

**Institution:** Rathinam Technical Campus (Autonomous), Coimbatore  
**Project:** Late-Event Correction & Daily Reporting System  
**Milestone:** Final 30% Development Milestone (Review 3)  

This directory contains visual and empirical engineering evidence answering the three critical gaps identified by the capstone review committee:
1. **Gap 1:** Database Schema Constraints, WAL Mode, Foreign Keys & Concurrency Safety
2. **Gap 2:** Performance Benchmarks, Replay Throughput, Latency Percentiles & Free-Tier Resource Footprint
3. **Gap 3:** Human-in-the-Loop Governance, Dynamic Justification, Rejection Reasons & Report Lineage

---

## Catalog of Visual Engineering Evidence

| Ref # | Screenshot Filename | Interface / Evidence View | Evaluator Requirement Addressed |
|---|---|---|---|
| **01** | `01_overview_dashboard.png` | Main System Overview Dashboard | Global health status, 4 academic domains, latency KPI counters, late event count |
| **02** | `02_event_stream.png` | Live Event Stream & Ingestion Queue | Real-time multi-domain ingestion, status badges (On-Time, Late, Duplicate, Invalid) |
| **03** | `03_late_event_detection.png` | Late Event Arrival vs Event-Time Detection | 24-hour watermark thresholding, delay calculation ($T_{\text{arrival}} - T_{\text{event}}$) |
| **04** | `04_historical_report_before_correction.png` | Historical Daily Report Prior to Correction | Baseline v1 snapshot showing uncorrected aggregates for past dates |
| **05** | `05_high_impact_correction.png` | High-Impact Drift Detection Card | Identification of >15% aggregate shift or high-risk academic status changes |
| **06** | `06_pending_review_queue.png` | Stakeholder Pending Review Queue | Centralized queue showing all flagged corrections awaiting human governance |
| **07** | `07_correction_detail.png` | Detailed Correction Comparison Card | 4-box aggregate diff (Before, Delta, Proposed, Impact %) + dynamic textual explanation |
| **08** | `08_approval_confirmation.png` | Governance Rejection / Approval Modal | Administrator review workflow with rejection reason capture and confirmation dialog |
| **09** | `09_corrected_historical_report.png` | Corrected Historical Report (v2 / v3) | Updated report reflecting applied delta with incremented version counter |
| **10** | `10_version_timeline.png` | Immutable Report Version Timeline | Chronological chain of report versions showing creator, timestamp, and delta |
| **11** | `11_audit_lineage.png` | Complete End-to-End Audit Lineage | Ordered audit trail from raw event ingestion to approval and final reporting |
| **12** | `12_rollback.png` | Atomic Rollback & Compensation View | Administrator-triggered reversal creating compensating v(N+1) snapshot |
| **13** | `13_reconciliation.png` | Ground-Truth Reconciliation Engine | 100.0% mathematical match proof against independent daily partition sums |
| **14** | `14_performance_dashboard.png` | Real-Time Performance Dashboard | Throughput (eps), average latency, P95/P99 latency, and heap memory footprint |
| **15** | `15_system_health.png` | Live System & Database Diagnostics | Active SQLite WAL mode check, foreign key enforcement, and busy timeout verification |
| **16** | `16_fastapi_swagger_schema.png` | OpenAPI / FastAPI Swagger Specification | Explicit Pydantic response models, HTTP 409 conflict contracts, and validation rules |
| **17** | `17_benchmark_result.png` | Multi-Scale Benchmark CLI Output | Terminal log of empirical scaling (100–5000 events) and 4-profile historical replay |
| **18** | `18_automated_test_result.png` | Automated Pytest Suite Execution | 29 passing automated tests covering concurrency, boundaries, transactions, and API |

---

## Verifiable Demonstration Highlights

1. **Deterministic State Transitions:**  
   Pending corrections cannot be approved twice or rejected after approval (enforced via HTTP 409 Conflict).
2. **Dynamic Natural Language Explanations:**  
   Every pending card dynamically constructs a grammatical sentence explaining domain, observed delay in hours, delta magnitude, and policy threshold violation without hardcoding.
3. **Database Concurrency Protection:**  
   Multi-threaded requests targeting identical events yield a single stored entity via `UNIQUE(event_id)`, while historical updates run in explicit `BEGIN IMMEDIATE` transaction boundaries with SQLite WAL mode enabled.
