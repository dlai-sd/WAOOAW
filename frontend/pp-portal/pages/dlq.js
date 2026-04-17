// frontend/pp-portal/pages/dlq.js
const API_BASE = typeof window !== 'undefined' ? (window.PP_API_BASE || '') : '';

export function renderDlqItem(task) {
  const errMsg = task.last_error ? task.last_error.slice(0, 100) : 'No error detail';
  return `
<div class="dlq-item" data-task-id="${task.id}">
  <div class="dlq-item__info">
    <span class="dlq-item__id">#${task.id.slice(0, 8)}</span>
    <span class="dlq-item__agent">${task.agent_name}</span>
    <span class="dlq-item__step">${task.step_name}</span>
    <span class="dlq-item__failures">${task.failure_count}× failed</span>
    <p class="dlq-item__error" title="${task.last_error || ''}">${errMsg}…</p>
  </div>
  <div class="dlq-item__actions">
    <button class="btn btn--cyan" onclick="requeueTask('${task.id}', this)">Requeue</button>
    <button class="btn btn--red" onclick="skipTask('${task.id}')">Skip</button>
  </div>
</div>`;
}

export async function loadDlq() {
  const base = typeof window !== 'undefined' ? (window.PP_API_BASE || '') : API_BASE;
  const res = await fetch(`${base}/v1/dlq?limit=50`);
  if (!res.ok) throw new Error('Failed to load DLQ');
  const tasks = await res.json();
  const container = document.getElementById('dlq-list');
  if (!tasks.length) {
    container.innerHTML = '<div class="empty-state empty-state--celebrate">🎉 Queue is clear — all agents running smoothly!</div>';
    return;
  }
  container.innerHTML = tasks.map(renderDlqItem).join('');
  updateNavBadge(tasks.length);
  if (typeof window !== 'undefined') {
    window.requeueTask = requeueTask;
    window.skipTask = skipTask;
  }
}

export async function requeueTask(taskId, btn) {
  btn.disabled = true;
  btn.nextElementSibling && (btn.nextElementSibling.disabled = true);
  const base = typeof window !== 'undefined' ? (window.PP_API_BASE || '') : API_BASE;
  const res = await fetch(`${base}/v1/dlq/${taskId}/requeue`, { method: 'POST' });
  if (!res.ok) {
    btn.disabled = false;
    btn.nextElementSibling && (btn.nextElementSibling.disabled = false);
    typeof alert !== 'undefined' && alert('Requeue failed');
    return;
  }
  document.querySelector(`[data-task-id="${taskId}"]`)?.remove();
}

export async function skipTask(taskId) {
  if (typeof confirm !== 'undefined' && !confirm('Skip this task permanently? It will not be retried.')) return;
  const base = typeof window !== 'undefined' ? (window.PP_API_BASE || '') : API_BASE;
  await fetch(`${base}/v1/dlq/${taskId}/skip`, { method: 'POST' });
  document.querySelector(`[data-task-id="${taskId}"]`)?.remove();
}

export function updateNavBadge(count) {
  const badge = document.getElementById('dlq-badge');
  if (badge) { badge.textContent = count; badge.hidden = count === 0; }
}

document.addEventListener('DOMContentLoaded', () =>
  loadDlq().catch(err => { document.getElementById('dlq-list').innerHTML = `<p class="error">${err.message}</p>`; })
);
