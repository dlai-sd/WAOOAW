// frontend/pp-portal/components/ComponentRunRow.js
const STATUS_ICONS = { completed: '✓', running: '⏳', failed: '✗', pending: '⏸' };
const STATUS_CLASSES = { completed: 'success', running: 'running', failed: 'error', pending: 'pending' };

export function renderComponentRunRow(cr) {
  const icon = STATUS_ICONS[cr.status] || '•';
  const cls = STATUS_CLASSES[cr.status] || 'pending';
  const errMsg = cr.error_message
    ? `<span class="cr-row__error" title="${cr.error_message}">${cr.error_message.slice(0, 80)}…</span>`
    : '';
  return `
<div class="cr-row cr-row--${cls}">
  <span class="cr-row__icon">${icon}</span>
  <span class="cr-row__step">${cr.step_name}</span>
  ${cr.duration_ms ? `<span class="cr-row__dur">${cr.duration_ms}ms</span>` : ''}
  ${errMsg}
</div>`;
}
