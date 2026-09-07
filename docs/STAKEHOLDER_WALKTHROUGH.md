# Stakeholder Walkthrough Guide — RATHINAM TECHNICAL CAMPUS

**Primary Stakeholder**: Rathinam Technical Campus Data Administrator / Reporting Manager

This document provides explicit answers and UI workflows for the 7 core operational questions.

---

### Question 1: Are today's reports accurate?
* **Dashboard Answer**: Check the **Ground Truth Match %** badge on the top header bar and Executive Overview card. A score of 100% confirms that all daily aggregates match ground truth with zero double counting.

### Question 2: How many late events have arrived?
* **Dashboard Answer**: Look at the **Late Events** metric card in the top header row or navigate to the **Live Event Stream** tab. Late events exceeding the 24-hour cutoff threshold are highlighted with yellow `LATE` badges.

### Question 3: Which previous reports were corrected?
* **Dashboard Answer**: Navigate to the **Daily Reports & Diff** tab. Look for entries tagged `CORRECTED` with green metrics showing the updated aggregate value and a version badge (e.g. `v2`, `v3`).

### Question 4: Why were they corrected?
* **Dashboard Answer**: Open the **Audit Trail & Lineage** tab or click **History** on any daily report card. The audit log lists explicit correction reasons such as *"Automated late-event delta correction"* or *"Backdated attendance submission"*.

### Question 5: Are any high-impact corrections waiting for review?
* **Dashboard Answer**: The **Pending Reviews** metric card flashes red when items await approval. Navigate to the **Pending Reviews** tab to see proposed metrics, impact percentages, and approve/reject controls.

### Question 6: Can every correction be traced through the audit trail?
* **Dashboard Answer**: Yes. Every event ingestion, duplicate discard, version bump, review approval, and rollback is recorded in the searchable **Audit Trail & Lineage Explorer** with full JSON details.

### Question 7: Can an incorrect correction be rolled back?
* **Dashboard Answer**: Yes. Open the **Rollback Manager** tab and click **Rollback**. The system executes a compensating action, restoring the prior report aggregate and creating a new version entry ($v_{current} \to v_{current+1}$).
