// frontend/pages/my-agents.js
import { renderAgentCard }       from '../components/AgentCard.js';
import { renderFlowRunTimeline } from '../components/FlowRunTimeline.js';
import { renderDeliverableCard } from '../components/DeliverableCard.js';

const API_BASE = typeof window !== 'undefined' ? (window.API_BASE || '') : '';
let pollingInterval = null;

export async function loadMyAgents() {
  const res = await fetch(`${API_BASE}/cp/hired-agents`);
  if (!res.ok) throw new Error('Failed to load agents');
  return await res.json();
}

export async function loadFlowRuns(hiredInstanceId) {
  try {
    const res = await fetch(`${API_BASE}/cp/flow-runs?hired_instance_id=${hiredInstanceId}`);
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export function renderApprovalBadge(flowRuns) {
  const pending = (flowRuns || []).find(fr => fr.status === 'awaiting_approval');
  return pending ? '<span class="badge badge--approval">Needs Approval</span>' : '';
}

export function renderAgentList(agents, flowRunsMap) {
  const list = document.getElementById('agent-list');
  if (!list) return;
  if (!agents.length) {
    list.innerHTML = '<div class="empty-state">You have no agents yet. <a href="/marketplace">Browse the marketplace</a> to get started.</div>';
    return;
  }
  list.innerHTML = agents.map(agent => {
    const flowRuns  = flowRunsMap[agent.id] || [];
    const latestRun = flowRuns[0] || null;
    const badge     = renderApprovalBadge(flowRuns);
    const card      = renderAgentCard({
      id: agent.id, name: agent.name, industry: agent.industry,
      status: latestRun?.status || 'paused',
      specialty: agent.specialty, rating: agent.rating, price: agent.price,
      ctaLabel: 'View Details', ctaHref: `#agent-${agent.id}`,
    });
    return `<div class="agent-list-item" data-agent-id="${agent.id}">${card}${badge}</div>`;
  }).join('');
}

export async function renderAgentDetail(agentId) {
  const panel = document.getElementById('agent-detail');
  if (!panel) return;
  const flowRuns  = await loadFlowRuns(agentId);
  const latestRun = flowRuns[0] || null;
  if (!latestRun) {
    panel.hidden = false;
    panel.innerHTML = '<p class="empty-state">No runs yet.</p>';
    return;
  }
  let componentRuns = [];
  try {
    const crRes = await fetch(`${API_BASE}/cp/component-runs?flow_run_id=${latestRun.id}`);
    if (crRes.ok) componentRuns = await crRes.json();
  } catch {}
  let deliverables = [];
  try {
    const dRes = await fetch(`${API_BASE}/cp/deliverables?flow_run_id=${latestRun.id}`);
    if (dRes.ok) deliverables = await dRes.json();
  } catch {}
  panel.hidden = false;
  panel.innerHTML = `
    <div class="agent-detail">
      <h3>Latest Run</h3>
      ${renderFlowRunTimeline(latestRun, componentRuns)}
      <h3>Deliverables</h3>
      ${deliverables.length
        ? deliverables.map(renderDeliverableCard).join('')
        : '<p class="empty-state">No deliverables yet.</p>'}
    </div>
  `;
  if (latestRun.status === 'running') {
    if (pollingInterval) clearInterval(pollingInterval);
    pollingInterval = setInterval(() => renderAgentDetail(agentId), 5000);
  }
}

export function init() {
  const list = document.getElementById('agent-list');
  loadMyAgents().then(async agents => {
    const flowRunsMap = {};
    await Promise.all(agents.map(async a => { flowRunsMap[a.id] = await loadFlowRuns(a.id); }));
    renderAgentList(agents, flowRunsMap);
  }).catch(err => {
    if (list) list.innerHTML = `<p class="error">${err.message}</p>`;
  });
}

document.addEventListener('DOMContentLoaded', init);
