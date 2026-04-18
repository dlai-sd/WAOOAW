// frontend/pages/approvals.js
import { renderApprovalQueueItem, approveFlowRun, rejectFlowRun }
  from '../components/ApprovalQueueItem.js';

const API_BASE = typeof window !== 'undefined' ? (window.API_BASE || '') : '';

export async function loadPendingApprovals() {
  const res = await fetch(`${API_BASE}/cp/flow-runs?status=awaiting_approval`);
  if (!res.ok) throw new Error('Failed to load approvals');
  return await res.json();
}

export function updateNavBadge(count) {
  const badge = document.getElementById('approvals-badge');
  if (badge) { badge.textContent = count; badge.hidden = count === 0; }
}

export async function renderApprovalList(flowRuns) {
  const container = document.getElementById('approval-list');
  if (!container) return;
  if (!flowRuns.length) {
    container.innerHTML = '<div class="empty-state empty-state--celebrate">🎉 All caught up — no pending approvals!</div>';
    return;
  }
  const items = await Promise.all(flowRuns.map(async fr => {
    let deliverable = null;
    try {
      const res = await fetch(`${API_BASE}/cp/deliverables?flow_run_id=${fr.id}&limit=1`);
      if (res.ok) { const list = await res.json(); deliverable = list[0] || null; }
    } catch {}
    return renderApprovalQueueItem(fr, deliverable, fr.agent_name || 'Agent');
  }));
  container.innerHTML = items.join('');
  updateNavBadge(flowRuns.length);
  if (typeof window !== 'undefined') {
    window.approveFlowRun = approveFlowRun;
    window.rejectFlowRun  = rejectFlowRun;
  }
}

export function init() {
  loadPendingApprovals()
    .then(renderApprovalList)
    .catch(err => {
      const container = document.getElementById('approval-list');
      if (container) container.innerHTML = `<p class="error">${err.message}</p>`;
    });
}

document.addEventListener('DOMContentLoaded', init);
