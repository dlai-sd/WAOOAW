// frontend/components/ApprovalQueueItem.js
const API_BASE = typeof window !== 'undefined' ? (window.API_BASE || '') : '';

export function renderApprovalQueueItem(flowRun, deliverable, agentName) {
  const preview = deliverable
    ? (deliverable.content?.per_platform_variants
        ? `Publish to platforms: ${Object.keys(deliverable.content.per_platform_variants).join(', ')}`
        : `Place trade: ${JSON.stringify(deliverable.content).slice(0, 80)}`)
    : 'Pending output preview';
  return `
<div class="approval-item" data-flow-run-id="${flowRun.id}">
  <div class="approval-item__agent">${agentName}</div>
  <p class="approval-item__preview">${preview}</p>
  <div class="approval-item__actions">
    <button class="btn btn--cyan" onclick="approveFlowRun('${flowRun.id}', this)">Approve</button>
    <button class="btn btn--red" onclick="rejectFlowRun('${flowRun.id}')">Reject</button>
  </div>
</div>`;
}

export async function approveFlowRun(flowRunId, btn) {
  btn.disabled = true;
  const base = typeof window !== 'undefined' ? (window.API_BASE || '') : '';
  const res = await fetch(`${base}/cp/approvals/${flowRunId}/approve`, { method: 'POST' });
  if (!res.ok) { btn.disabled = false; alert('Approval failed — try again'); return; }
  document.querySelector(`[data-flow-run-id="${flowRunId}"]`)?.remove();
}

export async function rejectFlowRun(flowRunId) {
  if (!confirm('Reject this agent output? The run will be marked as failed.')) return;
  const base = typeof window !== 'undefined' ? (window.API_BASE || '') : '';
  await fetch(`${base}/cp/approvals/${flowRunId}/reject`, { method: 'POST' });
  document.querySelector(`[data-flow-run-id="${flowRunId}"]`)?.remove();
}
