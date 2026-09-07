# Data Engineering Methodology — RATHINAM TECHNICAL CAMPUS

## 1. Baseline vs. Stateful Late-Event Correction Model

### Naive Baseline Snapshot Model
Traditional batch reporting computes daily aggregates at midnight on the arrival date:
$$A_{\text{baseline}}(D) = \sum \{ v(e) \mid e \in \text{ValidEvents}, \text{arrival\_date}(e) = D \}$$
If an event occurs on date $D$ but arrives on date $D + k$, it is either credited to date $D+k$ or lost from historical reports for date $D$.

### Stateful Late-Event Corrected Model
The dynamic correction engine routes events according to `event_timestamp.date()`:
$$A_{\text{corrected}}(D, t) = \sum \{ v(e) \mid e \in \text{ValidEvents}, \text{event\_date}(e) = D, \text{ingested\_by}(t) \}$$

### Independent Ground Truth Definition
Ground truth $A_{\text{GT}}(D)$ is computed independently by querying raw events grouped by `event_timestamp.date()`:
$$A_{\text{GT}}(D) = \sum \{ v(e) \mid e \in \text{ValidEvents}, \text{event\_date}(e) = D \}$$

### Verified Reconciliation Invariant
After all valid events for an experiment have arrived and been processed (and all reviews validated):
$$A_{\text{corrected}}(D) = A_{\text{GT}}(D) \quad \text{with } \text{Corrected Error} = 0.0000 \quad \forall D$$

---

## 2. Impact Percentage & High-Risk Thresholding

To distinguish single late events (+1 attendance) from high-impact batch updates or critical academic/placement alterations, the impact percentage is formulated as:

$$\text{Impact \%} = \begin{cases} 0.0 & \text{if } A_{\text{old}} = 0.0 \\ \frac{|A_{\text{new}} - A_{\text{old}}|}{\max(|A_{\text{old}}|, 10.0)} \times 100 & \text{if } A_{\text{old}} > 0.0 \end{cases}$$

A correction is tagged as **High Impact** if:
1. $\text{Impact \%} \ge \text{HIGH\_IMPACT\_THRESHOLD\_PERCENT}$ (15%) AND $|A_{\text{new}} - A_{\text{old}}| \ge 5.0$, OR
2. Event payload contains forced high-risk status (`is_high_risk_outcome` or `is_placement_status_change`).

---

## 3. Dynamic Review Approval & Compensating Rollback

### Review Approval
Upon Data Administrator approval of a pending correction, `review_pending_correction` dynamically computes the live sum across all valid events for date $D$:
$$A_{\text{approved}}(D) = \sum \{ v(e) \mid e \in \text{ValidEvents}, \text{event\_date}(e) = D \}$$
This avoids overwriting live aggregates with static draft snapshots.

### Compensating Rollback State Machine
1. Report version increments from $v_{k} \to v_{k+1}$.
2. A new `ReportVersion` record is appended with `change_type = 'ROLLBACK'`.
3. Target `ReportCorrection` status is updated to `ROLLED_BACK`.
4. Idempotency guard prevents rolling back an already rolled-back correction.
5. Historical version records $v_1, \dots, v_k$ are preserved intact.
