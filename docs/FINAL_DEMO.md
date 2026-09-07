# Final Evaluation Demonstration Script — RATHINAM TECHNICAL CAMPUS

**Title**: RATHINAM TECHNICAL CAMPUS — Late-Event Correction & Reporting System

---

## Controlled Demonstration Script (8-Step Scenario)

To perform an evaluator demonstration, open the dashboard at `http://localhost:3000` and click the **Run Demonstration** button on the top right header.

### Demonstration Walkthrough Sequence:

1. **Step 1: Create Initial Daily Report**
   - System creates initial August 20 Attendance report with 1 on-time event ($v1$, aggregate = 1.0).

2. **Step 2: Inject Normal Events**
   - Ingests 4 normal attendance events ($v2$, aggregate = 5.0).

3. **Step 3: Inject Late Attendance Event (76h Delay)**
   - Ingests event `DEMO-EVT-LATE-101` occurring on August 20 but arriving August 23.
   - Report auto-corrects aggregate from 5.0 to 6.0 ($v3$).

4. **Step 4: Duplicate Re-Injection (Idempotency Check)**
   - Re-injects `DEMO-EVT-LATE-101`.
   - Caught by `UNIQUE(event_id)` database constraint. Contribution +0. Aggregate remains 6.0. Zero double counting.

5. **Step 5: High-Impact Placement Change Injected**
   - Ingests late placement offer event marked as high-impact status change.
   - Status changes to `PENDING_REVIEW`. Queued in Review Queue.

6. **Step 6: Data Administrator Approval**
   - Administrator reviews and approves high-impact correction. Aggregate updates to version $v4$.

7. **Step 7: Inspect Audit Lineage**
   - Opens Audit Trail tab showing complete append-only event log.

8. **Step 8: Execute Compensating Rollback**
   - Triggers compensating rollback for correction `CORR-HI-IMPACT`.
   - Aggregate restored with new version entry ($v5$). Historical logs preserved intact.
