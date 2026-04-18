// frontend/pp-portal/pages/fleet.js
const API_BASE = typeof window !== 'undefined' ? (window.PP_API_BASE || '') : '';
let refreshTimer = null;

export function renderFleetAgentRow(agent, summary) {
  const errorRate = summary.total > 0
    ? ((summary.failed / summary.total) * 100).toFixed(1)
    : '0.0';
  const barWidth = (count, total) => total > 0 ? Math.round((count / total) * 100) : 0;
  return `
<div class="fleet-row" data-agent-id="${agent.id}">
  <div class="fleet-row__name">${agent.name}</div>
  <div class="fleet-row__instances">${agent.instance_count != null ? agent.instance_count : 0} instances</div>
  <div class="fleet-row__bars">
    <div class="fleet-bar fleet-bar--green" style="width:${barWidth(summary.completed, summary.total)}%"
         title="${summary.completed} completed"></div>
    <div class="fleet-bar fleet-bar--yellow" style="width:${barWidth(summary.running, summary.total)}%"
         title="${summary.running} running"></div>
    <div class="fleet-bar fleet-bar--red" style="width:${barWidth(summary.failed, summary.total)}%"
         title="${summary.failed} failed"></div>
  </div>
  <div class="fleet-row__error-rate ${parseFloat(errorRate) > 10 ? 'fleet-row__error-rate--high' : ''}">
    ${errorRate}% err
  </div>
  <a href="/pp/agent?id=${agent.id}" class="btn btn--outline fleet-row__drill">Details →</a>
</div>`;
}

export async function loadFleet() {
  const base = typeof window !== 'undefined' ? (window.PP_API_BASE || '') : API_BASE;
  const agentsRes = await fetch(`${base}/v1/agents`);
  if (!agentsRes.ok) throw new Error('Failed to load agents');
  const agents = await agentsRes.json();
  const summaries = await Promise.all(
    agents.map(a => fetch(`${base}/v1/component-runs/summary?agent_id=${a.id}`)
      .then(r => r.ok ? r.json() : { total: 0, running: 0, completed: 0, failed: 0 })
    )
  );
  const grid = document.getElementById('fleet-grid');
  if (!agents.length) { grid.innerHTML = '<p class="empty-state">No agents deployed yet.</p>'; return; }
  grid.innerHTML = agents.map((a, i) => renderFleetAgentRow(a, summaries[i])).join('');
}

export function startPolling() {
  loadFleet().catch(err => { document.getElementById('fleet-grid').innerHTML = `<p class="error">${err.message}</p>`; });
  refreshTimer = typeof setInterval !== 'undefined'
    ? setInterval(() => loadFleet().catch(console.error), 10000)
    : null;
}

document.addEventListener('DOMContentLoaded', startPolling);
