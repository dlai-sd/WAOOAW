// frontend/pages/hire.js
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
  const res = await fetch(`${base}/cp/hired-agents`, {
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
  const res = await fetch(`${base}/cp/skill-configs/${wizardState.hiredInstanceId}/default`, {
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
  const res = await fetch(`${base}/cp/goal-instances`, {
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
