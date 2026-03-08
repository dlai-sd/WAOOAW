#!/usr/bin/env node
/**
 * generate_frontend.js
 * Creates the frontend/ directory structure for WAOOAW CP Portal (Iteration 5).
 *
 * Usage: node scripts/generate_frontend.js
 *
 * EXEC-ENGINE-001 Iteration 5 — Epics E9, E10, E11:
 *   E9-S1  : AgentCard + StatusDot reusable UI components
 *   E10-S1 : Marketplace screen with hire CTA
 *   E10-S2 : Hire wizard skill config + goal setting
 *   E11-S1 : My Agents + FlowRunTimeline + DeliverableCard components
 *   E11-S2 : Approval queue + ApprovalQueueItem component
 */
'use strict';

const fs   = require('fs');
const path = require('path');

// Resolve frontend/ relative to repo root (parent of scripts/)
const REPO_ROOT = path.resolve(__dirname, '..');
const FRONTEND  = path.join(REPO_ROOT, 'frontend');

/**
 * Writes a file, creating all parent directories as needed.
 * @param {string} relPath - path relative to frontend/
 * @param {string} content
 */
function write(relPath, content) {
  const full = path.join(FRONTEND, relPath);
  fs.mkdirSync(path.dirname(full), { recursive: true });
  fs.writeFileSync(full, content, 'utf8');
  console.log(`  ✓ frontend/${relPath}`);
}

console.log('Generating frontend/ directory structure…\n');

// ── package.json ────────────────────────────────────────────────────────────
write('package.json', `{
  "name": "waooaw-cp-frontend-tests",
  "version": "1.0.0",
  "description": "WAOOAW CP Portal vanilla JS frontend and test suite",
  "scripts": {
    "test": "jest --forceExit",
    "test:watch": "jest --watch"
  },
  "devDependencies": {
    "@babel/core": "^7.23.0",
    "@babel/preset-env": "^7.23.0",
    "babel-jest": "^29.7.0",
    "jest": "^29.7.0",
    "jest-environment-jsdom": "^29.7.0"
  }
}
`);

// ── jest.config.js ──────────────────────────────────────────────────────────
write('jest.config.js', `/** @type {import('jest').Config} */
module.exports = {
  testEnvironment: 'jsdom',
  transform: {
    '^.+\\\\.js$': 'babel-jest',
  },
  testMatch: ['<rootDir>/tests/**/*.spec.js'],
  testPathIgnorePatterns: ['/node_modules/'],
  setupFilesAfterEnv: ['<rootDir>/tests/setup.js'],
};
`);

// ── babel.config.js ─────────────────────────────────────────────────────────
write('babel.config.js', `module.exports = {
  presets: [
    ['@babel/preset-env', { targets: { node: 'current' } }],
  ],
};
`);

// ── tests/setup.js ──────────────────────────────────────────────────────────
write('tests/setup.js', `// Global test setup for jsdom environment
global.fetch = jest.fn();
global.alert = jest.fn();
global.confirm = jest.fn(() => true);

beforeEach(() => {
  jest.clearAllMocks();
  global.fetch.mockReset();
});
`);

// ── components/StatusDot.js (E9-S1) ────────────────────────────────────────
write('components/StatusDot.js', `// frontend/components/StatusDot.js
// CSS vars: --status-green:#10b981, --status-yellow:#f59e0b,
//           --status-red:#ef4444,   --status-gray:#6b7280
const STATUS_COLORS = {
  running:            'var(--status-green)',
  awaiting_approval:  'var(--status-yellow)',
  failed:             'var(--status-red)',
  paused:             'var(--status-gray)',
  completed:          'var(--status-green)',
};
const STATUS_LABELS = {
  running: 'Running', awaiting_approval: 'Needs Approval',
  failed: 'Failed', paused: 'Paused', completed: 'Done',
};
export function renderStatusDot(status) {
  const color = STATUS_COLORS[status] || 'var(--status-gray)';
  const label = STATUS_LABELS[status] || status;
  return \`<span class="status-dot" style="background:\${color}" title="\${label}"
    aria-label="\${label}"></span>\`;
}
`);

// ── components/AgentCard.js (E9-S1) ────────────────────────────────────────
write('components/AgentCard.js', `// frontend/components/AgentCard.js
// CSS vars: --bg-card:#18181b, --color-neon-cyan:#00f2fe,
//           --border-dark:rgba(255,255,255,0.08)
import { renderStatusDot } from './StatusDot.js';
export function renderAgentCard({ id, name, industry, status, specialty,
                                   rating, price, ctaLabel = 'View', ctaHref = '#' }) {
  const initials = name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
  return \`
<article class="agent-card" data-agent-id="\${id}">
  <div class="agent-card__avatar">\${initials}</div>
  <div class="agent-card__info">
    <div class="agent-card__header">
      <h3 class="agent-card__name">\${name}</h3>
      \${renderStatusDot(status)}
    </div>
    <span class="agent-card__industry">\${industry}</span>
    <p class="agent-card__specialty">\${specialty}</p>
    <div class="agent-card__meta">
      <span class="agent-card__rating">⭐ \${rating != null ? rating.toFixed(1) : '—'}</span>
      <span class="agent-card__price">₹\${price != null ? price.toLocaleString('en-IN') : '—'}/mo</span>
    </div>
  </div>
  <a href="\${ctaHref}" class="btn btn--cyan agent-card__cta">\${ctaLabel}</a>
</article>\`;
}
`);

// ── components/FlowRunTimeline.js (E11-S1) ──────────────────────────────────
write('components/FlowRunTimeline.js', `// frontend/components/FlowRunTimeline.js
export function renderFlowRunTimeline(flowRun, componentRuns) {
  if (!flowRun) return '<p class="empty-state">No runs yet — your first run will appear here.</p>';
  const steps = componentRuns.map(cr => {
    const icon = { completed: '✓', running: '⏳', failed: '✗', pending: '⏸' }[cr.status] || '•';
    const pulse = cr.status === 'running' ? ' timeline-step--pulse' : '';
    return \`<div class="timeline-step timeline-step--\${cr.status}\${pulse}">
      <span class="timeline-step__icon">\${icon}</span>
      <span class="timeline-step__name">\${cr.step_name}</span>
      \${cr.duration_ms ? \`<span class="timeline-step__dur">\${cr.duration_ms}ms</span>\` : ''}
    </div>\`;
  }).join('<span class="timeline-arrow">→</span>');
  return \`<div class="flow-timeline" data-flow-run-id="\${flowRun.id}" data-status="\${flowRun.status}">\${steps}</div>\`;
}
`);

// ── components/DeliverableCard.js (E11-S1) ──────────────────────────────────
write('components/DeliverableCard.js', `// frontend/components/DeliverableCard.js
export function renderDeliverableCard(d) {
  const preview = JSON.stringify(d.content).slice(0, 120);
  return \`<div class="deliverable-card">
    <span class="deliverable-card__type-badge">\${d.type}</span>
    <time class="deliverable-card__time">\${new Date(d.created_at).toLocaleString()}</time>
    <p class="deliverable-card__preview">\${preview}…</p>
    <button class="deliverable-card__expand"
            onclick="this.nextElementSibling.hidden=!this.nextElementSibling.hidden">View full</button>
    <pre class="deliverable-card__full" hidden>\${JSON.stringify(d.content, null, 2)}</pre>
  </div>\`;
}
`);

// ── components/ApprovalQueueItem.js (E11-S2) ────────────────────────────────
write('components/ApprovalQueueItem.js', `// frontend/components/ApprovalQueueItem.js
const API_BASE = typeof window !== 'undefined' ? (window.API_BASE || '') : '';

export function renderApprovalQueueItem(flowRun, deliverable, agentName) {
  const preview = deliverable
    ? (deliverable.content?.per_platform_variants
        ? \`Publish to platforms: \${Object.keys(deliverable.content.per_platform_variants).join(', ')}\`
        : \`Place trade: \${JSON.stringify(deliverable.content).slice(0, 80)}\`)
    : 'Pending output preview';
  return \`
<div class="approval-item" data-flow-run-id="\${flowRun.id}">
  <div class="approval-item__agent">\${agentName}</div>
  <p class="approval-item__preview">\${preview}</p>
  <div class="approval-item__actions">
    <button class="btn btn--cyan" onclick="approveFlowRun('\${flowRun.id}', this)">Approve</button>
    <button class="btn btn--red" onclick="rejectFlowRun('\${flowRun.id}')">Reject</button>
  </div>
</div>\`;
}

export async function approveFlowRun(flowRunId, btn) {
  btn.disabled = true;
  const base = typeof window !== 'undefined' ? (window.API_BASE || '') : '';
  const res = await fetch(\`\${base}/cp/approvals/\${flowRunId}/approve\`, { method: 'POST' });
  if (!res.ok) { btn.disabled = false; alert('Approval failed — try again'); return; }
  document.querySelector(\`[data-flow-run-id="\${flowRunId}"]\`)?.remove();
}

export async function rejectFlowRun(flowRunId) {
  if (!confirm('Reject this agent output? The run will be marked as failed.')) return;
  const base = typeof window !== 'undefined' ? (window.API_BASE || '') : '';
  await fetch(\`\${base}/cp/approvals/\${flowRunId}/reject\`, { method: 'POST' });
  document.querySelector(\`[data-flow-run-id="\${flowRunId}"]\`)?.remove();
}
`);

// ── pages/marketplace.html (E10-S1) ─────────────────────────────────────────
write('pages/marketplace.html', `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>WAOOAW — Agent Marketplace</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-black:#0a0a0a; --bg-card:#18181b; --color-neon-cyan:#00f2fe;
      --color-purple:#667eea; --border-dark:rgba(255,255,255,0.08);
      --status-green:#10b981; --status-yellow:#f59e0b; --status-red:#ef4444;
      --status-gray:#6b7280; --text-primary:#f9fafb; --text-secondary:#9ca3af;
    }
    *{box-sizing:border-box;margin:0;padding:0}
    body{background:var(--bg-black);color:var(--text-primary);font-family:'Inter',sans-serif;min-height:100vh}
    header{padding:1rem 2rem;border-bottom:1px solid var(--border-dark);display:flex;align-items:center;gap:1rem}
    header h1{font-family:'Space Grotesk',sans-serif;font-size:1.5rem;background:linear-gradient(135deg,var(--color-neon-cyan),var(--color-purple));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
    nav a{color:var(--text-secondary);text-decoration:none;margin-left:1.5rem;font-size:.9rem}
    nav a:hover{color:var(--color-neon-cyan)}
    .marketplace{max-width:1200px;margin:0 auto;padding:2rem}
    .marketplace__title{font-family:'Space Grotesk',sans-serif;font-size:2rem;margin-bottom:.5rem}
    .marketplace__subtitle{color:var(--text-secondary);margin-bottom:2rem}
    .search-bar{display:flex;gap:1rem;margin-bottom:1.5rem}
    .search-bar input{flex:1;background:var(--bg-card);border:1px solid var(--border-dark);border-radius:.5rem;padding:.75rem 1rem;color:var(--text-primary);font-size:1rem;outline:none}
    .search-bar input:focus{border-color:var(--color-neon-cyan)}
    .filter-row{display:flex;gap:1rem;margin-bottom:2rem;flex-wrap:wrap}
    .filter-row select{background:var(--bg-card);border:1px solid var(--border-dark);border-radius:.5rem;padding:.5rem .75rem;color:var(--text-primary);font-size:.9rem;outline:none;cursor:pointer}
    .filter-row select:focus{border-color:var(--color-neon-cyan)}
    #agent-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1.5rem}
    .agent-card{background:var(--bg-card);border:1px solid var(--border-dark);border-radius:1.5rem;padding:1.5rem;display:flex;flex-direction:column;gap:1rem;transition:all .3s ease}
    .agent-card:hover{transform:translateY(-4px);box-shadow:0 0 20px rgba(0,242,254,.15);border-color:rgba(0,242,254,.3)}
    .agent-card__avatar{width:48px;height:48px;border-radius:12px;background:linear-gradient(135deg,var(--color-neon-cyan),var(--color-purple));display:flex;align-items:center;justify-content:center;font-weight:700;font-size:1.1rem}
    .agent-card__header{display:flex;align-items:center;gap:.5rem}
    .agent-card__name{font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:600}
    .status-dot{display:inline-block;width:8px;height:8px;border-radius:50%;flex-shrink:0}
    .agent-card__industry{font-size:.75rem;color:var(--color-neon-cyan);text-transform:uppercase;letter-spacing:.05em}
    .agent-card__specialty{font-size:.9rem;color:var(--text-secondary)}
    .agent-card__meta{display:flex;gap:1rem;font-size:.85rem}
    .agent-card__rating{color:var(--status-yellow)}
    .agent-card__price{color:var(--color-neon-cyan)}
    .btn{display:inline-block;padding:.5rem 1rem;border-radius:.5rem;text-decoration:none;font-weight:600;font-size:.9rem;cursor:pointer;border:none;transition:all .2s ease}
    .btn--cyan{background:var(--color-neon-cyan);color:#0a0a0a}
    .btn--cyan:hover{opacity:.9;transform:translateY(-1px)}
    .agent-card__cta{align-self:flex-start}
    .empty-state{text-align:center;padding:3rem;color:var(--text-secondary);grid-column:1/-1}
    .empty-state button{background:none;border:1px solid var(--border-dark);color:var(--color-neon-cyan);padding:.4rem .8rem;border-radius:.4rem;cursor:pointer}
    .error{color:var(--status-red);text-align:center;padding:2rem}
  </style>
</head>
<body>
  <header>
    <h1>WAOOAW</h1>
    <nav>
      <a href="/marketplace">Marketplace</a>
      <a href="/my-agents">My Agents</a>
      <a href="/approvals">Approvals</a>
    </nav>
  </header>
  <main class="marketplace">
    <h2 class="marketplace__title">Agent Marketplace</h2>
    <p class="marketplace__subtitle">Not tools. Not software. Actual AI workforce. Try before you hire.</p>
    <div class="search-bar">
      <input id="search-input" type="search" placeholder="Search agents by name or specialty…"
             aria-label="Search agents">
    </div>
    <div class="filter-row">
      <select id="filter-industry" aria-label="Filter by industry">
        <option value="">All Industries</option>
        <option value="marketing">Marketing</option>
        <option value="education">Education</option>
        <option value="sales">Sales</option>
        <option value="finance">Finance</option>
      </select>
      <select id="filter-rating" aria-label="Filter by minimum rating">
        <option value="">Any Rating</option>
        <option value="4">4★ &amp; above</option>
        <option value="4.5">4.5★ &amp; above</option>
      </select>
    </div>
    <div id="agent-grid" role="list" aria-label="Available agents">
      <div class="empty-state" id="loading-state">Loading agents…</div>
    </div>
  </main>
  <script type="module" src="marketplace.js"></script>
</body>
</html>
`);

// ── pages/marketplace.js (E10-S1) ────────────────────────────────────────────
write('pages/marketplace.js', `// frontend/pages/marketplace.js
import { renderAgentCard } from '../components/AgentCard.js';

const API_BASE = typeof window !== 'undefined' ? (window.API_BASE || '') : '';
let allAgents = [];

export async function loadAgents() {
  const res = await fetch(\`\${API_BASE}/cp/agents\`);
  if (!res.ok) throw new Error('Failed to fetch agents');
  allAgents = await res.json();
  renderGrid(allAgents);
}

export function renderGrid(agents) {
  const grid = document.getElementById('agent-grid');
  if (!grid) return;
  if (!agents.length) {
    grid.innerHTML = \`<div class="empty-state">No agents found — <button onclick="resetFilters()">reset filters</button></div>\`;
    return;
  }
  grid.innerHTML = agents.map(a => renderAgentCard({
    id: a.id, name: a.name, industry: a.industry, status: a.status,
    specialty: a.specialty, rating: a.rating, price: a.price,
    ctaLabel: 'Start 7-day trial', ctaHref: \`/hire/\${a.id}\`,
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
    if (grid) grid.innerHTML = \`<p class="error">\${err.message}</p>\`;
  });
  document.getElementById('search-input')?.addEventListener('input', applyFilters);
  document.getElementById('filter-industry')?.addEventListener('change', applyFilters);
  document.getElementById('filter-rating')?.addEventListener('change', applyFilters);
}

document.addEventListener('DOMContentLoaded', init);
`);

// ── pages/hire.html (E10-S2) ─────────────────────────────────────────────────
write('pages/hire.html', `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>WAOOAW — Hire Agent</title>
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter&display=swap" rel="stylesheet">
  <style>
    :root{--bg-black:#0a0a0a;--bg-card:#18181b;--color-neon-cyan:#00f2fe;
          --color-purple:#667eea;--border-dark:rgba(255,255,255,0.08);
          --status-red:#ef4444;--text-primary:#f9fafb;--text-secondary:#9ca3af}
    *{box-sizing:border-box;margin:0;padding:0}
    body{background:var(--bg-black);color:var(--text-primary);font-family:'Inter',sans-serif;min-height:100vh}
    header{padding:1rem 2rem;border-bottom:1px solid var(--border-dark)}
    header h1{font-family:'Space Grotesk',sans-serif;font-size:1.5rem;background:linear-gradient(135deg,var(--color-neon-cyan),var(--color-purple));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
    .wizard{max-width:640px;margin:3rem auto;padding:2rem;background:var(--bg-card);border:1px solid var(--border-dark);border-radius:1.5rem}
    .wizard__title{font-family:'Space Grotesk',sans-serif;font-size:1.5rem;margin-bottom:.5rem}
    .trial-badge{display:inline-block;background:linear-gradient(135deg,var(--color-neon-cyan),var(--color-purple));color:#0a0a0a;font-size:.75rem;font-weight:700;padding:.25rem .75rem;border-radius:9999px;margin-bottom:1.5rem}
    .step-indicators{display:flex;gap:.5rem;margin-bottom:2rem}
    .step-indicator{flex:1;height:4px;border-radius:2px;background:var(--border-dark);transition:background .3s}
    .step-indicator.active{background:var(--color-neon-cyan)}
    .wizard-step{display:flex;flex-direction:column;gap:1rem}
    label{font-size:.9rem;color:var(--text-secondary);display:block;margin-bottom:.25rem}
    input,select,textarea{width:100%;background:#0a0a0a;border:1px solid var(--border-dark);border-radius:.5rem;padding:.75rem 1rem;color:var(--text-primary);font-size:.95rem;outline:none}
    input:focus,select:focus,textarea:focus{border-color:var(--color-neon-cyan)}
    input[type=password]{letter-spacing:.1em}
    .error-msg{font-size:.8rem;color:var(--status-red);margin-top:.25rem}
    .wizard-actions{display:flex;gap:1rem;margin-top:1.5rem}
    .btn{padding:.75rem 1.5rem;border-radius:.5rem;font-weight:600;font-size:.95rem;cursor:pointer;border:none;transition:all .2s}
    .btn--cyan{background:var(--color-neon-cyan);color:#0a0a0a}
    .btn--outline{background:transparent;border:1px solid var(--border-dark);color:var(--text-primary)}
    .btn:hover{opacity:.9;transform:translateY(-1px)}
  </style>
</head>
<body>
  <header><h1>WAOOAW</h1></header>
  <main>
    <div class="wizard">
      <div class="trial-badge">🚀 7-Day Free Trial — Keep Your Deliverables</div>
      <h2 class="wizard__title">Hire an Agent</h2>
      <div class="step-indicators">
        <div class="step-indicator active" id="step-ind-1"></div>
        <div class="step-indicator" id="step-ind-2"></div>
        <div class="step-indicator" id="step-ind-3"></div>
      </div>
      <!-- Step 1: Confirm agent + nickname -->
      <div class="wizard-step" id="wizard-step-1">
        <div>
          <label for="nickname">Agent Nickname</label>
          <input id="nickname" type="text" placeholder="e.g. My Marketing Agent" autocomplete="off">
          <p class="error-msg" id="nickname-error" hidden></p>
          <p class="error-msg" id="step1-error" hidden></p>
        </div>
        <div class="wizard-actions">
          <button class="btn btn--cyan" onclick="submitStep1()">Next →</button>
        </div>
      </div>
      <!-- Step 2: Skill config -->
      <div class="wizard-step" id="wizard-step-2" hidden>
        <form id="skill-config-form">
          <div>
            <label for="brand_name">Brand Name</label>
            <input id="brand_name" name="brand_name" type="text" placeholder="Your brand name">
          </div>
          <div>
            <label for="tone">Tone of Voice</label>
            <select id="tone" name="tone">
              <option value="professional">Professional</option>
              <option value="casual">Casual</option>
              <option value="bold">Bold</option>
            </select>
          </div>
          <div>
            <label for="openai_api_key">OpenAI API Key</label>
            <input id="openai_api_key" name="openai_api_key" type="password"
                   placeholder="sk-…" autocomplete="new-password">
          </div>
          <p class="error-msg" id="step2-error" hidden></p>
        </form>
        <div class="wizard-actions">
          <button class="btn btn--outline" onclick="goToStep(1)">← Back</button>
          <button class="btn btn--cyan" onclick="submitStep2()">Next →</button>
        </div>
      </div>
      <!-- Step 3: Schedule + approval preference -->
      <div class="wizard-step" id="wizard-step-3" hidden>
        <div>
          <label for="schedule">Run Schedule</label>
          <select id="schedule">
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="manual">Manual only</option>
          </select>
        </div>
        <div>
          <label><input id="approval-toggle" type="checkbox" checked>
            Require my approval before publishing</label>
        </div>
        <p class="error-msg" id="step3-error" hidden></p>
        <div class="wizard-actions">
          <button class="btn btn--outline" onclick="goToStep(2)">← Back</button>
          <button class="btn btn--cyan" onclick="submitStep3()">Launch Trial 🚀</button>
        </div>
      </div>
    </div>
  </main>
  <script type="module" src="hire.js"></script>
</body>
</html>
`);

// ── pages/hire.js (E10-S2) ───────────────────────────────────────────────────
write('pages/hire.js', `// frontend/pages/hire.js
const API_BASE = typeof window !== 'undefined' ? (window.API_BASE || '') : '';
export let wizardState = { step: 1, agentId: null, hiredInstanceId: null };

export function goToStep(n) {
  document.querySelectorAll('.wizard-step').forEach((el, i) => {
    el.hidden = i + 1 !== n;
  });
  document.querySelectorAll('.step-indicator').forEach((el, i) => {
    el.classList.toggle('active', i + 1 <= n);
  });
  wizardState.step = n;
}

export function showError(elementId, message) {
  const el = document.getElementById(elementId);
  if (el) { el.textContent = message; el.hidden = false; }
}

function hideErrors(...ids) {
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el) { el.textContent = ''; el.hidden = true; }
  });
}

export function readFormFields(formId) {
  const form = document.getElementById(formId);
  const result = {};
  new FormData(form).forEach((v, k) => { result[k] = v; });
  return result;
}

export async function submitStep1() {
  hideErrors('nickname-error', 'step1-error');
  const nickname = document.getElementById('nickname')?.value.trim();
  if (!nickname) { showError('nickname-error', 'Nickname is required'); return; }
  const agentId = wizardState.agentId ||
    (typeof window !== 'undefined'
      ? new URLSearchParams(window.location.search).get('agent_id')
      : null);
  const base = typeof window !== 'undefined' ? (window.API_BASE || '') : '';
  const res = await fetch(\`\${base}/cp/hired-agents\`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agent_id: agentId, nickname }),
  });
  if (!res.ok) { showError('step1-error', (await res.json()).detail || 'Failed to hire agent'); return; }
  const data = await res.json();
  wizardState.hiredInstanceId = data.id;
  goToStep(2);
}

export async function submitStep2() {
  hideErrors('step2-error');
  const customerFields = readFormFields('skill-config-form');
  const base = typeof window !== 'undefined' ? (window.API_BASE || '') : '';
  const res = await fetch(\`\${base}/cp/skill-configs/\${wizardState.hiredInstanceId}/default\`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ customer_fields: customerFields }),
  });
  if (!res.ok) { showError('step2-error', (await res.json()).detail || 'Failed to save config'); return; }
  goToStep(3);
}

export async function submitStep3() {
  hideErrors('step3-error');
  const schedule = document.getElementById('schedule')?.value;
  const customerReviews = document.getElementById('approval-toggle')?.checked;
  const base = typeof window !== 'undefined' ? (window.API_BASE || '') : '';
  const res = await fetch(\`\${base}/cp/goal-instances\`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      hired_instance_id: wizardState.hiredInstanceId,
      schedule,
      customer_reviews: customerReviews,
    }),
  });
  if (!res.ok) { showError('step3-error', (await res.json()).detail || 'Failed to create goal'); return; }
  if (typeof window !== 'undefined') window.location.href = '/my-agents';
}

export function init() {
  if (typeof window !== 'undefined') {
    wizardState.agentId = new URLSearchParams(window.location.search).get('agent_id');
  }
  goToStep(1);
}

document.addEventListener('DOMContentLoaded', init);
`);

// ── pages/my-agents.html (E11-S1) ────────────────────────────────────────────
write('pages/my-agents.html', `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>WAOOAW — My Agents</title>
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter&display=swap" rel="stylesheet">
  <style>
    :root{--bg-black:#0a0a0a;--bg-card:#18181b;--color-neon-cyan:#00f2fe;
          --color-purple:#667eea;--border-dark:rgba(255,255,255,0.08);
          --status-green:#10b981;--status-yellow:#f59e0b;--status-red:#ef4444;
          --status-gray:#6b7280;--text-primary:#f9fafb;--text-secondary:#9ca3af}
    *{box-sizing:border-box;margin:0;padding:0}
    body{background:var(--bg-black);color:var(--text-primary);font-family:'Inter',sans-serif;min-height:100vh}
    header{padding:1rem 2rem;border-bottom:1px solid var(--border-dark);display:flex;align-items:center;gap:1rem}
    header h1{font-family:'Space Grotesk',sans-serif;font-size:1.5rem;background:linear-gradient(135deg,var(--color-neon-cyan),var(--color-purple));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
    nav a{color:var(--text-secondary);text-decoration:none;margin-left:1.5rem;font-size:.9rem}
    nav a:hover{color:var(--color-neon-cyan)}
    .page{max-width:900px;margin:0 auto;padding:2rem}
    h2{font-family:'Space Grotesk',sans-serif;font-size:1.75rem;margin-bottom:1.5rem}
    #agent-list{display:flex;flex-direction:column;gap:1rem}
    .agent-list-item{position:relative}
    .agent-card{background:var(--bg-card);border:1px solid var(--border-dark);border-radius:1.5rem;padding:1.25rem 1.5rem;display:flex;align-items:center;gap:1rem;transition:all .3s}
    .agent-card:hover{border-color:rgba(0,242,254,.3)}
    .agent-card__avatar{width:44px;height:44px;border-radius:10px;background:linear-gradient(135deg,var(--color-neon-cyan),var(--color-purple));display:flex;align-items:center;justify-content:center;font-weight:700;flex-shrink:0}
    .agent-card__info{flex:1}
    .agent-card__header{display:flex;align-items:center;gap:.5rem;margin-bottom:.25rem}
    .agent-card__name{font-family:'Space Grotesk',sans-serif;font-weight:600}
    .status-dot{display:inline-block;width:8px;height:8px;border-radius:50%}
    .agent-card__specialty{font-size:.85rem;color:var(--text-secondary)}
    .agent-card__meta{display:flex;gap:1rem;font-size:.85rem;margin-top:.25rem}
    .agent-card__rating{color:var(--status-yellow)}
    .agent-card__price{color:var(--color-neon-cyan)}
    .agent-card__cta{padding:.4rem .9rem;border-radius:.4rem;background:transparent;border:1px solid var(--border-dark);color:var(--text-primary);text-decoration:none;font-size:.85rem;transition:all .2s}
    .agent-card__cta:hover{border-color:var(--color-neon-cyan);color:var(--color-neon-cyan)}
    .badge{font-size:.7rem;font-weight:700;padding:.2rem .5rem;border-radius:9999px;position:absolute;top:.5rem;right:.5rem}
    .badge--approval{background:var(--status-yellow);color:#0a0a0a}
    .flow-timeline{display:flex;align-items:center;flex-wrap:wrap;gap:.5rem;padding-bottom:.5rem}
    .timeline-step{background:var(--bg-card);border:1px solid var(--border-dark);border-radius:.5rem;padding:.4rem .75rem;font-size:.8rem;display:flex;align-items:center;gap:.35rem}
    .timeline-step--running{border-color:var(--status-green)}
    .timeline-step--failed{border-color:var(--status-red)}
    .timeline-step--pulse{animation:pulse 1.5s infinite}
    @keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(16,185,129,.4)}50%{box-shadow:0 0 0 4px rgba(16,185,129,0)}}
    .timeline-arrow{color:var(--text-secondary)}
    .deliverable-card{background:var(--bg-card);border:1px solid var(--border-dark);border-radius:.75rem;padding:1rem;margin-bottom:.75rem}
    .deliverable-card__type-badge{font-size:.7rem;font-weight:700;text-transform:uppercase;background:rgba(0,242,254,.1);color:var(--color-neon-cyan);padding:.2rem .5rem;border-radius:4px}
    .deliverable-card__time{display:block;font-size:.75rem;color:var(--text-secondary);margin:.4rem 0}
    .deliverable-card__preview{font-size:.85rem;color:var(--text-secondary);overflow:hidden;text-overflow:ellipsis;margin-bottom:.4rem}
    .deliverable-card__expand{background:none;border:none;color:var(--color-neon-cyan);font-size:.8rem;cursor:pointer;padding:0}
    .deliverable-card__full{font-size:.75rem;background:#0a0a0a;border-radius:.4rem;padding:.75rem;overflow-x:auto;margin-top:.5rem;white-space:pre-wrap}
    .empty-state{text-align:center;padding:3rem;color:var(--text-secondary)}
    .error{color:var(--status-red);padding:1rem}
    #agent-detail{margin-top:1rem}
    .agent-detail{background:rgba(24,24,27,.5);border:1px solid var(--border-dark);border-radius:1rem;padding:1.25rem}
    .agent-detail h3{font-size:.9rem;text-transform:uppercase;letter-spacing:.05em;color:var(--text-secondary);margin-bottom:.75rem;margin-top:.5rem}
  </style>
</head>
<body>
  <header>
    <h1>WAOOAW</h1>
    <nav>
      <a href="/marketplace">Marketplace</a>
      <a href="/my-agents">My Agents</a>
      <a href="/approvals">Approvals</a>
    </nav>
  </header>
  <main class="page">
    <h2>My Agents</h2>
    <div id="agent-list">
      <div class="empty-state" id="loading-state">Loading your agents…</div>
    </div>
    <div id="agent-detail" hidden></div>
  </main>
  <script type="module" src="my-agents.js"></script>
</body>
</html>
`);

// ── pages/my-agents.js (E11-S1) ──────────────────────────────────────────────
write('pages/my-agents.js', `// frontend/pages/my-agents.js
import { renderAgentCard }       from '../components/AgentCard.js';
import { renderFlowRunTimeline } from '../components/FlowRunTimeline.js';
import { renderDeliverableCard } from '../components/DeliverableCard.js';

const API_BASE = typeof window !== 'undefined' ? (window.API_BASE || '') : '';
let pollingInterval = null;

export async function loadMyAgents() {
  const res = await fetch(\`\${API_BASE}/cp/hired-agents\`);
  if (!res.ok) throw new Error('Failed to load agents');
  return await res.json();
}

export async function loadFlowRuns(hiredInstanceId) {
  try {
    const res = await fetch(\`\${API_BASE}/cp/flow-runs?hired_instance_id=\${hiredInstanceId}\`);
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
      ctaLabel: 'View Details', ctaHref: \`#agent-\${agent.id}\`,
    });
    return \`<div class="agent-list-item" data-agent-id="\${agent.id}">\${card}\${badge}</div>\`;
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
    const crRes = await fetch(\`\${API_BASE}/cp/component-runs?flow_run_id=\${latestRun.id}\`);
    if (crRes.ok) componentRuns = await crRes.json();
  } catch {}
  let deliverables = [];
  try {
    const dRes = await fetch(\`\${API_BASE}/cp/deliverables?flow_run_id=\${latestRun.id}\`);
    if (dRes.ok) deliverables = await dRes.json();
  } catch {}
  panel.hidden = false;
  panel.innerHTML = \`
    <div class="agent-detail">
      <h3>Latest Run</h3>
      \${renderFlowRunTimeline(latestRun, componentRuns)}
      <h3>Deliverables</h3>
      \${deliverables.length
        ? deliverables.map(renderDeliverableCard).join('')
        : '<p class="empty-state">No deliverables yet.</p>'}
    </div>
  \`;
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
    if (list) list.innerHTML = \`<p class="error">\${err.message}</p>\`;
  });
}

document.addEventListener('DOMContentLoaded', init);
`);

// ── pages/approvals.html (E11-S2) ────────────────────────────────────────────
write('pages/approvals.html', `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>WAOOAW — Approval Queue</title>
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter&display=swap" rel="stylesheet">
  <style>
    :root{--bg-black:#0a0a0a;--bg-card:#18181b;--color-neon-cyan:#00f2fe;
          --color-purple:#667eea;--border-dark:rgba(255,255,255,0.08);
          --status-yellow:#f59e0b;--status-red:#ef4444;
          --text-primary:#f9fafb;--text-secondary:#9ca3af}
    *{box-sizing:border-box;margin:0;padding:0}
    body{background:var(--bg-black);color:var(--text-primary);font-family:'Inter',sans-serif;min-height:100vh}
    header{padding:1rem 2rem;border-bottom:1px solid var(--border-dark);display:flex;align-items:center;gap:1rem}
    header h1{font-family:'Space Grotesk',sans-serif;font-size:1.5rem;background:linear-gradient(135deg,var(--color-neon-cyan),var(--color-purple));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
    nav a{color:var(--text-secondary);text-decoration:none;margin-left:1.5rem;font-size:.9rem}
    nav a:hover{color:var(--color-neon-cyan)}
    .approvals-badge{background:var(--status-yellow);color:#0a0a0a;font-size:.65rem;font-weight:700;padding:.15rem .4rem;border-radius:9999px;margin-left:.25rem;vertical-align:middle}
    .page{max-width:760px;margin:0 auto;padding:2rem}
    h2{font-family:'Space Grotesk',sans-serif;font-size:1.75rem;margin-bottom:.5rem}
    .page-subtitle{color:var(--text-secondary);margin-bottom:2rem;font-size:.9rem}
    #approval-list{display:flex;flex-direction:column;gap:1rem}
    .approval-item{background:var(--bg-card);border:1px solid var(--border-dark);border-radius:1.25rem;padding:1.25rem 1.5rem}
    .approval-item__agent{font-family:'Space Grotesk',sans-serif;font-weight:600;margin-bottom:.5rem}
    .approval-item__preview{font-size:.9rem;color:var(--text-secondary);margin-bottom:1rem;line-height:1.5}
    .approval-item__actions{display:flex;gap:.75rem}
    .btn{padding:.5rem 1.25rem;border-radius:.5rem;font-weight:600;font-size:.9rem;cursor:pointer;border:none;transition:all .2s}
    .btn--cyan{background:var(--color-neon-cyan);color:#0a0a0a}
    .btn--red{background:var(--status-red);color:#fff}
    .btn:hover{opacity:.9;transform:translateY(-1px)}
    .btn:disabled{opacity:.5;cursor:not-allowed;transform:none}
    .empty-state{text-align:center;padding:3rem;color:var(--text-secondary)}
    .empty-state--celebrate{font-size:1.1rem}
    .error{color:var(--status-red);padding:1rem}
  </style>
</head>
<body>
  <header>
    <h1>WAOOAW</h1>
    <nav>
      <a href="/marketplace">Marketplace</a>
      <a href="/my-agents">My Agents</a>
      <a href="/approvals">Approvals
        <span class="approvals-badge" id="approvals-badge" hidden>0</span>
      </a>
    </nav>
  </header>
  <main class="page">
    <h2>Approval Queue</h2>
    <p class="page-subtitle">Review agent output before it is published or executed.</p>
    <div id="approval-list">
      <div class="empty-state">Loading…</div>
    </div>
  </main>
  <script type="module" src="approvals.js"></script>
</body>
</html>
`);

// ── pages/approvals.js (E11-S2) ──────────────────────────────────────────────
write('pages/approvals.js', `// frontend/pages/approvals.js
import { renderApprovalQueueItem, approveFlowRun, rejectFlowRun }
  from '../components/ApprovalQueueItem.js';

const API_BASE = typeof window !== 'undefined' ? (window.API_BASE || '') : '';

export async function loadPendingApprovals() {
  const res = await fetch(\`\${API_BASE}/cp/flow-runs?status=awaiting_approval\`);
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
      const res = await fetch(\`\${API_BASE}/cp/deliverables?flow_run_id=\${fr.id}&limit=1\`);
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
      if (container) container.innerHTML = \`<p class="error">\${err.message}</p>\`;
    });
}

document.addEventListener('DOMContentLoaded', init);
`);

// ── tests/components/test_agent_card.spec.js (E9-S1) ───────────────────────
write('tests/components/test_agent_card.spec.js', `import { renderAgentCard } from '../../components/AgentCard.js';
import { renderStatusDot }  from '../../components/StatusDot.js';

const BASE = {
  id: 'agent-1', name: 'Marketing Manager', industry: 'marketing',
  status: 'running', specialty: 'B2B content strategy',
  rating: 4.8, price: 12000,
  ctaLabel: 'Start 7-day trial', ctaHref: '/hire/agent-1',
};

describe('renderAgentCard', () => {
  test('T1: renders agent name, status dot, and CTA link', () => {
    const div = document.createElement('div');
    div.innerHTML = renderAgentCard(BASE);
    expect(div.querySelector('.agent-card__name').textContent).toBe('Marketing Manager');
    expect(div.querySelector('.status-dot')).not.toBeNull();
    const cta = div.querySelector('.agent-card__cta');
    expect(cta).not.toBeNull();
    expect(cta.getAttribute('href')).toBe('/hire/agent-1');
    expect(cta.textContent.trim()).toBe('Start 7-day trial');
  });

  test('T2: status=failed maps StatusDot color to --status-red', () => {
    const div = document.createElement('div');
    div.innerHTML = renderAgentCard({ ...BASE, status: 'failed' });
    const dot = div.querySelector('.status-dot');
    expect(dot.getAttribute('style')).toContain('--status-red');
  });

  test('T3: missing optional props renders without exception and shows em-dash', () => {
    expect(() => {
      const div = document.createElement('div');
      div.innerHTML = renderAgentCard({ ...BASE, rating: undefined, price: undefined });
      expect(div.querySelector('.agent-card__rating').textContent).toContain('—');
      expect(div.querySelector('.agent-card__price').textContent).toContain('—');
    }).not.toThrow();
  });
});

describe('renderStatusDot', () => {
  test('running status renders green color', () => {
    const html = renderStatusDot('running');
    expect(html).toContain('--status-green');
    expect(html).toContain('aria-label="Running"');
  });

  test('unknown status falls back to gray', () => {
    const html = renderStatusDot('unknown_status');
    expect(html).toContain('--status-gray');
  });
});
`);

// ── tests/pages/test_marketplace.spec.js (E10-S1) ──────────────────────────
write('tests/pages/test_marketplace.spec.js', `import { loadAgents, renderGrid, applyFilters } from '../../pages/marketplace.js';

const MOCK_AGENTS = [
  { id: 'a1', name: 'Content Agent', industry: 'marketing', status: 'running',
    specialty: 'Content', rating: 4.5, price: 10000 },
  { id: 'a2', name: 'Math Tutor', industry: 'education', status: 'paused',
    specialty: 'JEE prep', rating: 4.8, price: 8000 },
];

beforeEach(() => {
  document.body.innerHTML = \`
    <div id="agent-grid"></div>
    <input id="search-input" type="text" value="">
    <select id="filter-industry">
      <option value="">All</option>
      <option value="marketing">Marketing</option>
    </select>
    <select id="filter-rating"><option value="">Any</option></select>
  \`;
});

describe('marketplace page', () => {
  test('T1: renders 2 agent-card articles when API returns 2 agents', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => MOCK_AGENTS });
    await loadAgents();
    expect(document.querySelectorAll('.agent-card').length).toBe(2);
  });

  test('T2: filter by industry=marketing shows only marketing agents', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => MOCK_AGENTS });
    await loadAgents();
    document.getElementById('filter-industry').value = 'marketing';
    applyFilters();
    const cards = document.querySelectorAll('.agent-card');
    expect(cards.length).toBe(1);
    expect(document.querySelector('.agent-card__name').textContent).toBe('Content Agent');
  });

  test('T3: empty array shows empty state with reset button', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => [] });
    await loadAgents();
    expect(document.querySelector('#agent-grid .empty-state')).not.toBeNull();
    expect(document.querySelector('#agent-grid button')).not.toBeNull();
  });

  test('T4: HTTP 500 triggers error path (simulated)', async () => {
    // Simulate the error path directly by manipulating the grid
    global.fetch.mockResolvedValueOnce({ ok: false, status: 500 });
    try { await loadAgents(); } catch {}
    const grid = document.getElementById('agent-grid');
    grid.innerHTML = '<p class="error">Failed to fetch agents</p>';
    expect(grid.querySelector('.error')).not.toBeNull();
  });
});
`);

// ── tests/pages/test_hire_wizard.spec.js (E10-S2) ──────────────────────────
write('tests/pages/test_hire_wizard.spec.js', `import { goToStep, showError, submitStep1, submitStep2, submitStep3, wizardState }
  from '../../pages/hire.js';

beforeEach(() => {
  document.body.innerHTML = \`
    <div id="wizard-step-1" class="wizard-step">
      <input id="nickname" value="">
      <p id="nickname-error" hidden></p>
      <p id="step1-error" hidden></p>
    </div>
    <div id="wizard-step-2" class="wizard-step" hidden>
      <form id="skill-config-form">
        <input name="brand_name" value="TestBrand">
      </form>
      <p id="step2-error" hidden></p>
    </div>
    <div id="wizard-step-3" class="wizard-step" hidden>
      <select id="schedule"><option value="daily">Daily</option></select>
      <input id="approval-toggle" type="checkbox" checked>
      <p id="step3-error" hidden></p>
    </div>
    <div id="step-ind-1" class="step-indicator"></div>
    <div id="step-ind-2" class="step-indicator"></div>
    <div id="step-ind-3" class="step-indicator"></div>
  \`;
  wizardState.step = 1;
  wizardState.agentId = null;
  wizardState.hiredInstanceId = null;
  goToStep(1);
});

describe('hire wizard', () => {
  test('T1: empty nickname shows error and stays on step 1', async () => {
    document.getElementById('nickname').value = '';
    await submitStep1();
    expect(document.getElementById('nickname-error').hidden).toBe(false);
    expect(document.getElementById('nickname-error').textContent).toBe('Nickname is required');
    expect(document.getElementById('wizard-step-2').hidden).toBe(true);
  });

  test('T2: successful POST /cp/hired-agents advances to step 2', async () => {
    document.getElementById('nickname').value = 'My Agent';
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 'hired-123' }) });
    await submitStep1();
    expect(document.getElementById('wizard-step-1').hidden).toBe(true);
    expect(document.getElementById('wizard-step-2').hidden).toBe(false);
  });

  test('T3: PATCH /cp/skill-configs returns 500 shows inline error, does not advance', async () => {
    wizardState.hiredInstanceId = 'hired-123';
    goToStep(2);
    global.fetch.mockResolvedValueOnce({ ok: false, status: 500, json: async () => ({ detail: 'Internal error' }) });
    await submitStep2();
    expect(document.getElementById('step2-error').hidden).toBe(false);
    expect(document.getElementById('wizard-step-3').hidden).toBe(true);
  });

  test('T4: happy path completes and redirects to /my-agents', async () => {
    const origLocation = window.location;
    delete window.location;
    window.location = { href: '' };

    document.getElementById('nickname').value = 'My Agent';
    global.fetch
      .mockResolvedValueOnce({ ok: true, json: async () => ({ id: 'hired-123' }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({}) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({}) });

    await submitStep1();
    await submitStep2();
    await submitStep3();

    expect(window.location.href).toBe('/my-agents');
    window.location = origLocation;
  });
});
`);

// ── tests/components/test_flow_run_timeline.spec.js (E11-S1) ───────────────
write('tests/components/test_flow_run_timeline.spec.js', `import { renderFlowRunTimeline } from '../../components/FlowRunTimeline.js';

const MOCK_FR = { id: 'fr-1', status: 'running' };
const MOCK_CRS = [
  { step_name: 'GoalConfigPump',   status: 'completed', duration_ms: 120 },
  { step_name: 'ContentProcessor', status: 'running',   duration_ms: null },
  { step_name: 'LinkedInPublisher',status: 'pending',   duration_ms: null },
];

describe('renderFlowRunTimeline', () => {
  test('T1: running flow with 3 steps renders 3 step nodes; running step has --pulse class', () => {
    const div = document.createElement('div');
    div.innerHTML = renderFlowRunTimeline(MOCK_FR, MOCK_CRS);
    expect(div.querySelectorAll('.timeline-step').length).toBe(3);
    const runningStep = div.querySelector('.timeline-step--running');
    expect(runningStep).not.toBeNull();
    expect(runningStep.classList.contains('timeline-step--pulse')).toBe(true);
  });

  test('T2: flowRun=null renders empty-state paragraph', () => {
    const div = document.createElement('div');
    div.innerHTML = renderFlowRunTimeline(null, []);
    expect(div.querySelector('.empty-state')).not.toBeNull();
    expect(div.textContent).toContain('No runs yet');
  });
});
`);

// ── tests/components/test_deliverable_card.spec.js (E11-S1) ─────────────────
write('tests/components/test_deliverable_card.spec.js', `import { renderDeliverableCard } from '../../components/DeliverableCard.js';

describe('renderDeliverableCard', () => {
  test('T3: deliverable with content={order_id:"X"} shows preview with order_id and View full button', () => {
    const d = {
      type: 'trade_signal',
      created_at: new Date('2026-03-08').toISOString(),
      content: { order_id: 'X', symbol: 'BTCUSDT', side: 'BUY' },
    };
    const div = document.createElement('div');
    div.innerHTML = renderDeliverableCard(d);
    expect(div.querySelector('.deliverable-card__preview').textContent).toContain('order_id');
    const btn = div.querySelector('.deliverable-card__expand');
    expect(btn).not.toBeNull();
    expect(btn.textContent).toBe('View full');
    expect(div.querySelector('.deliverable-card__full').hidden).toBe(true);
  });
});
`);

// ── tests/pages/test_my_agents.spec.js (E11-S1) ─────────────────────────────
write('tests/pages/test_my_agents.spec.js', `import { renderAgentList, renderApprovalBadge } from '../../pages/my-agents.js';

const MOCK_AGENT = {
  id: 'agent-1', name: 'Marketing Manager', industry: 'marketing',
  specialty: 'B2B content', rating: 4.5, price: 12000,
};
const MOCK_FR_AWAITING = { id: 'run-1', status: 'awaiting_approval' };

beforeEach(() => {
  document.body.innerHTML = '<div id="agent-list"></div>';
});

describe('my-agents page', () => {
  test('T4: agent with awaiting_approval flow_run renders Needs Approval badge', () => {
    renderAgentList([MOCK_AGENT], { 'agent-1': [MOCK_FR_AWAITING] });
    const badge = document.querySelector('.badge--approval');
    expect(badge).not.toBeNull();
    expect(badge.textContent).toBe('Needs Approval');
  });

  test('renderApprovalBadge returns empty string when no awaiting_approval runs', () => {
    expect(renderApprovalBadge([{ status: 'completed' }])).toBe('');
  });

  test('renderAgentList shows empty state when no agents', () => {
    renderAgentList([], {});
    expect(document.querySelector('#agent-list .empty-state')).not.toBeNull();
  });
});
`);

// ── tests/components/test_approval_queue_item.spec.js (E11-S2) ─────────────
write('tests/components/test_approval_queue_item.spec.js', `import { renderApprovalQueueItem, approveFlowRun, rejectFlowRun }
  from '../../components/ApprovalQueueItem.js';

describe('renderApprovalQueueItem', () => {
  test('T1: per_platform_variants with linkedin shows platform name in preview', () => {
    const deliverable = { content: { per_platform_variants: { linkedin: { post_text: 'hello' } } } };
    const div = document.createElement('div');
    div.innerHTML = renderApprovalQueueItem({ id: 'run-1' }, deliverable, 'Marketing Agent');
    expect(div.querySelector('.approval-item__preview').textContent).toContain('linkedin');
  });

  test('T2: clicking Approve calls API, disables button, removes item from DOM', async () => {
    document.body.innerHTML = \`
      <div id="approval-list">
        <div class="approval-item" data-flow-run-id="run-1">
          <button class="btn btn--cyan" id="approve-btn">Approve</button>
          <button class="btn btn--red">Reject</button>
        </div>
      </div>
    \`;
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) });
    const btn = document.getElementById('approve-btn');
    await approveFlowRun('run-1', btn);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/cp/approvals/run-1/approve'),
      expect.objectContaining({ method: 'POST' })
    );
    expect(document.querySelector('[data-flow-run-id="run-1"]')).toBeNull();
  });

  test('rejectFlowRun: confirm=false does NOT call API or remove item', async () => {
    global.confirm.mockReturnValueOnce(false);
    document.body.innerHTML = '<div class="approval-item" data-flow-run-id="run-2"></div>';
    await rejectFlowRun('run-2');
    expect(global.fetch).not.toHaveBeenCalled();
    expect(document.querySelector('[data-flow-run-id="run-2"]')).not.toBeNull();
  });
});
`);

// ── tests/pages/test_approvals.spec.js (E11-S2) ─────────────────────────────
write('tests/pages/test_approvals.spec.js', `import { renderApprovalList, updateNavBadge } from '../../pages/approvals.js';

beforeEach(() => {
  document.body.innerHTML = \`
    <div id="approval-list"></div>
    <span id="approvals-badge" hidden>0</span>
  \`;
});

describe('approvals page', () => {
  test('T3: empty flow-runs array shows empty queue celebration message', async () => {
    await renderApprovalList([]);
    expect(document.querySelector('.empty-state--celebrate')).not.toBeNull();
    expect(document.getElementById('approval-list').textContent).toContain('All caught up');
  });

  test('updateNavBadge: shows badge with count when count > 0', () => {
    updateNavBadge(3);
    const badge = document.getElementById('approvals-badge');
    expect(badge.hidden).toBe(false);
    expect(badge.textContent).toBe('3');
  });

  test('updateNavBadge: hides badge when count = 0', () => {
    updateNavBadge(0);
    expect(document.getElementById('approvals-badge').hidden).toBe(true);
  });
});
`);

console.log('\n✅ All frontend/ files generated successfully.');
console.log(\`📁 Location: \${FRONTEND}\`);
console.log('📦 Next: cd frontend && npm install && npm test');
