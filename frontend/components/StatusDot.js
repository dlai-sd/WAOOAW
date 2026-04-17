// frontend/components/StatusDot.js
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
  return `<span class="status-dot" style="background:${color}" title="${label}"
    aria-label="${label}"></span>`;
}
