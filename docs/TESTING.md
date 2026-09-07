# Testing Strategy & Specifications — RATHINAM TECHNICAL CAMPUS

## 1. Test Overview

The system includes a 100% automated test suite using `pytest` located in `backend/tests/`.

### Summary of Test Execution:
```bash
py -m pytest -v
```
Output: **11 passed out of 11 tests** (100% clean execution).

---

## 2. Test Specifications

### Unit & Integration Tests
1. `test_pipeline.py`:
   - `test_on_time_event_ingestion`: Verifies `is_late == False` when delay $\le 24$h.
   - `test_late_event_ingestion`: Verifies `is_late == True` when delay $> 24$h.
   - `test_idempotency_duplicate_discard`: Verifies exact duplicate `event_id` is caught by DB constraint and logged as `DISCARD_DUPLICATE` with zero aggregate contribution.
   - `test_invalid_payload_handling`: Verifies corrupt/missing payloads are tagged `is_valid == False` and logged as `DISCARD_INVALID`.

2. `test_correction.py`:
   - `test_on_time_correction_and_ground_truth`: Verifies ground truth calculation equals on-time aggregate sum.
   - `test_late_event_recalculation`: Verifies late events update historical reporting date aggregate and bump version from $v1 \to v2 \to v3$.
   - `test_high_impact_forced_review`: Verifies forced placement status changes enter `PENDING_REVIEW` queue.

3. `test_audit_rollback.py`:
   - `test_rollback_compensating_action`: Verifies compensating rollback reverts report aggregate to prior state and increments version number.
   - `test_rollback_idempotency_guard`: Verifies attempting to rollback an already rolled back correction returns `ALREADY_ROLLED_BACK`.

4. `test_integration.py` (`test_full_end_to_end_integration_flow`):
   - Generates 150 synthetic events across 4 RTC domains.
   - Ingests events, processes late corrections, introduces duplicates, approves pending reviews, and triggers rollbacks.
   - Asserts system integrity and audit log completeness.

5. `test_reconciliation.py` (`test_final_corrected_aggregate_equals_ground_truth`):
   - **Mandatory Reconciliation Test**: Asserts `CorrectedAggregate(D) == GroundTruth(D)` across EVERY reporting date $D$ after all valid events have arrived and been processed.
