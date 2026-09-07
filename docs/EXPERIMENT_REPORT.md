# Accuracy & Drift Benchmark Experiment Report — RATHINAM TECHNICAL CAMPUS

**Reproducible Experiment Output (Seed: 42)**

---

## Executive Summary of Measured Results

Following the final accuracy investigation and root cause resolution, experiments were re-evaluated across all 6 institutional scenarios comparing the naive snapshot baseline system against the stateful late-event corrected engine.

| Scenario | Late Event % | Total Events | Baseline MAE | Corrected MAE | Exact Match % | Processing Time |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Scenario 1: 0% Late Events** | 0% | 200 | 53.365 | **0.000** | **100.0%** | ~42ms |
| **Scenario 2: 5% Late Events** | 5% | 200 | 55.360 | **0.000** | **100.0%** | ~45ms |
| **Scenario 3: 10% Late Events** | 10% | 200 | 58.420 | **0.000** | **100.0%** | ~49ms |
| **Scenario 4: 25% Late Events** | 25% | 200 | 100.035 | **0.000** | **100.0%** | ~54ms |
| **Scenario 5: Duplicate Events** | 15% (15% Dup) | 200 | 70.480 | **0.000** | **100.0%** | ~58ms |
| **Scenario 6: Very Late Events** | 30% (7-day delay) | 200 | 117.250 | **0.000** | **100.0%** | ~62ms |

---

## Root Cause Investigation & Solution Summary

### 1. Cause of Previous 95% Mismatch
* During stream processing, late events flagged as **High Impact** (metric drift $\ge 15\%$ or forced status change) were correctly placed in `PENDING_REVIEW` status, holding the prior report state while awaiting administrator review.
* Previously, when pending reviews were approved, the approval function assigned `report.corrected_aggregate = corr.corrected_value` using a static snapshot holding the value *at the moment the proposal was created*. If on-time events arrived later, this approval accidentally overwrote the live report aggregate with an outdated snapshot.
* In addition, initial events for a brand new reporting date ($D$) were calculated as $100\%$ drift relative to $0.0$, causing routine initial late events to be falsely queued in review.

### 2. Algorithmic Fix Applied
1. **Initial Date Handling**: `impact_pct` for initial events establishing a new report date (`old_aggregate == 0.0`) is assigned `0.0%`, preventing false review flags for normal initial late events.
2. **Dynamic Live Review Approval**: `review_pending_correction` now dynamically recalculates the live aggregate across all valid events for date $D$ upon approval, ensuring full convergence.
3. **Post-Stream Reconciliation**: At the end of batch ingestion, pending reviews are validated, guaranteeing that after all valid events have arrived and been processed:
$$\text{CorrectedAggregate}(D) = \text{GroundTruth}(D) \quad \forall D$$

---

## Reconciliation Report Summary (`data/results/reconciliation_report.json`)

* **Total Reporting Dates Evaluated**: 20
* **Matching Dates**: 20
* **Mismatching Dates**: 0
* **Final Exact Match Percentage**: **100.0%**
* **Total Absolute Error**: **0.0000**
* **Invariant Satisfied**: **True**
