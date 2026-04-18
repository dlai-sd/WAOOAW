// frontend/pp-portal/pages/agent-detail.js
import { renderComponentRunRow } from '../components/ComponentRunRow.js';
const API_BASE = typeof window !== 'undefined' ? (window.PP_API_BASE || '') : '';

export async function loadAgentDetail(agentId) {
  const base = typeof window !== 'undefined' ? (window.PP_API_BASE || '') : API_BASE;
  const runsRes = await fetch(`${base}/v1/flow-runs?agent_id=${agentId}&limit=10`);
  if (!runsRes.ok) throw new Error('Failed to load flow runs');
  const flowRuns = await runsRes.json();
  const list = document.getElementById('flow-run-list');
  if (!flowRuns.length) { list.innerHTML = '<p class="empty-state">No runs yet for this agent.</p>'; return; }
  list.innerHTML = flowRuns.map(fr => `
<details class="flow-run-item">
  <summary class="flow-run-item__summary">
    <span class="flow-run-item__status flow-run-item__status--${fr.status}">${fr.status}</span>
    <time>${fr.created_at ? new Date(fr.created_at).toLocaleString() : ''}</time>
  </summary>
  <div class="flow-run-item__steps" data-flow-run-id="${fr.id}">Loading steps…</div>
</details>`).join('');

  list.addEventListener('toggle', async (e) => {
    const details = e.target.closest('details');
    if (!details || !e.target.open) return;
    const stepsDiv = details.querySelector('[data-flow-run-id]');
    const flowRunId = stepsDiv && stepsDiv.dataset.flowRunId;
    if (!flowRunId) return;
    const base2 = typeof window !== 'undefined' ? (window.PP_API_BASE || '') : API_BASE;
    const crRes = await fetch(`${base2}/v1/component-runs?flow_run_id=${flowRunId}`);
    const componentRuns = crRes.ok ? await crRes.json() : [];
    stepsDiv.innerHTML = componentRuns.map(renderComponentRunRow).join('') || '<em>No steps recorded.</em>';
  }, true);
}

const agentId = typeof window !== 'undefined'
  ? new URLSearchParams(window.location.search).get('id')
  : null;
document.addEventListener('DOMContentLoaded', () => agentId && loadAgentDetail(agentId)
  .catch(err => { document.getElementById('flow-run-list').innerHTML = `<p class="error">${err.message}</p>`; }));
