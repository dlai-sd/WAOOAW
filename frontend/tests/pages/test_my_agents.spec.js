import { renderAgentList, renderApprovalBadge } from '../../pages/my-agents.js';

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
