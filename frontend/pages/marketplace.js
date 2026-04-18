// frontend/pages/marketplace.js
import { renderAgentCard } from '../components/AgentCard.js';

const API_BASE = typeof window !== 'undefined' ? (window.API_BASE || '') : '';
let allAgents = [];

export async function loadAgents() {
  const res = await fetch(`${API_BASE}/cp/agents`);
  if (!res.ok) throw new Error('Failed to fetch agents');
  allAgents = await res.json();
  renderGrid(allAgents);
}

export function renderGrid(agents) {
  const grid = document.getElementById('agent-grid');
  if (!grid) return;
  if (!agents.length) {
    grid.innerHTML = `<div class="empty-state">No agents found — <button onclick="resetFilters()">reset filters</button></div>`;
    return;
  }
  grid.innerHTML = agents.map(a => renderAgentCard({
    id: a.id, name: a.name, industry: a.industry, status: a.status,
    specialty: a.specialty, rating: a.rating, price: a.price,
    ctaLabel: 'Start 7-day trial', ctaHref: `/hire/${a.id}`,
  })).join('');
}

export function applyFilters() {
  const query  = (document.getElementById('search-input')?.value || '').toLowerCase();
  const ind    = document.getElementById('filter-industry')?.value || '';
  const minRat = parseFloat(document.getElementById('filter-rating')?.value || 0);
  const filtered = allAgents.filter(a =>
    (a.name.toLowerCase().includes(query) || a.specialty.toLowerCase().includes(query)) &&
    (!ind || a.industry === ind) &&
    (a.rating >= minRat)
  );
  renderGrid(filtered);
}

export function resetFilters() {
  const si = document.getElementById('search-input');
  const fi = document.getElementById('filter-industry');
  const fr = document.getElementById('filter-rating');
  if (si) si.value = '';
  if (fi) fi.value = '';
  if (fr) fr.value = '';
  renderGrid(allAgents);
}

export function init() {
  loadAgents().catch(err => {
    const grid = document.getElementById('agent-grid');
    if (grid) grid.innerHTML = `<p class="error">${err.message}</p>`;
  });
  document.getElementById('search-input')?.addEventListener('input', applyFilters);
  document.getElementById('filter-industry')?.addEventListener('change', applyFilters);
  document.getElementById('filter-rating')?.addEventListener('change', applyFilters);
}

document.addEventListener('DOMContentLoaded', init);
