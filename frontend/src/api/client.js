const API_BASE = '/api';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function fetchMetricsSummary() {
  const res = await fetch(`${API_BASE}/metrics/summary`);
  return res.json();
}

export async function fetchEvents(domain = '', isLate = null) {
  let url = `${API_BASE}/events?limit=100`;
  if (domain) url += `&domain=${encodeURIComponent(domain)}`;
  if (isLate !== null) url += `&is_late=${isLate}`;
  const res = await fetch(url);
  return res.json();
}

export async function ingestEvent(eventPayload) {
  const res = await fetch(`${API_BASE}/events/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(eventPayload),
  });
  return res.json();
}

export async function fetchDailyReports(domain = '', date = '') {
  let url = `${API_BASE}/reports`;
  const params = [];
  if (domain) params.push(`domain=${encodeURIComponent(domain)}`);
  if (date) params.push(`date=${encodeURIComponent(date)}`);
  if (params.length > 0) url += `?${params.join('&')}`;
  const res = await fetch(url);
  return res.json();
}

export async function fetchReportVersions(reportId) {
  const res = await fetch(`${API_BASE}/reports/${encodeURIComponent(reportId)}/versions`);
  return res.json();
}

export async function fetchPendingReviews() {
  const res = await fetch(`${API_BASE}/reviews/pending`);
  return res.json();
}

export async function handleReviewAction(correctionId, action, reviewerName = 'RTC Data Administrator') {
  const res = await fetch(`${API_BASE}/reviews/action`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      correction_id: correctionId,
      action: action,
      reviewer_name: reviewerName
    }),
  });
  return res.json();
}

export async function fetchAuditLogs(domain = '', action = '') {
  let url = `${API_BASE}/audit?limit=100`;
  if (domain) url += `&domain=${encodeURIComponent(domain)}`;
  if (action) url += `&action=${encodeURIComponent(action)}`;
  const res = await fetch(url);
  return res.json();
}

export async function fetchRollbackableCorrections() {
  const res = await fetch(`${API_BASE}/rollback/corrections`);
  return res.json();
}

export async function triggerRollback(correctionId, reason = 'Data Administrator Manual Rollback') {
  const res = await fetch(`${API_BASE}/rollback/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      correction_id: correctionId,
      reason: reason,
      actor: 'RTC Data Administrator'
    }),
  });
  return res.json();
}

export async function runControlledDemo() {
  const res = await fetch(`${API_BASE}/demo/run`, {
    method: 'POST'
  });
  return res.json();
}

export async function fetchReconciliationReport() {
  const res = await fetch(`${API_BASE}/reconciliation`);
  return res.json();
}

export async function fetchExperimentScenarios() {
  const res = await fetch(`${API_BASE}/experiments/scenarios`);
  return res.json();
}

export async function runExperimentsOnDemand() {
  const res = await fetch(`${API_BASE}/experiments/run`, {
    method: 'POST'
  });
  return res.json();
}
