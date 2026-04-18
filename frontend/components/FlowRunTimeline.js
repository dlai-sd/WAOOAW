// frontend/components/FlowRunTimeline.js
export function renderFlowRunTimeline(flowRun, componentRuns) {
  if (!flowRun) return '<p class="empty-state">No runs yet — your first run will appear here.</p>';
  const steps = componentRuns.map(cr => {
    const icon = { completed: '✓', running: '⏳', failed: '✗', pending: '⏸' }[cr.status] || '•';
    const pulse = cr.status === 'running' ? ' timeline-step--pulse' : '';
    return `<div class="timeline-step timeline-step--${cr.status}${pulse}">
      <span class="timeline-step__icon">${icon}</span>
      <span class="timeline-step__name">${cr.step_name}</span>
      ${cr.duration_ms ? `<span class="timeline-step__dur">${cr.duration_ms}ms</span>` : ''}
    </div>`;
  }).join('<span class="timeline-arrow">→</span>');
  return `<div class="flow-timeline" data-flow-run-id="${flowRun.id}" data-status="${flowRun.status}">${steps}</div>`;
}
