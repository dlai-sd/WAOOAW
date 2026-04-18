import { loadAgentDetail } from '../../pp-portal/pages/agent-detail.js';

const MOCK_FLOW_RUNS = [
  { id: 'fr-1', status: 'completed', created_at: '2026-03-08T10:00:00Z' },
  { id: 'fr-2', status: 'failed',    created_at: '2026-03-08T09:00:00Z' },
];
const MOCK_COMPONENT_RUNS = [
  { step_name: 'Pump',      status: 'completed', duration_ms: 200 },
  { step_name: 'Processor', status: 'failed',    duration_ms: 300, error_message: 'Bad signal' },
];

beforeEach(() => {
  document.body.innerHTML = '<div id="flow-run-list"></div>';
});

describe('loadAgentDetail', () => {
  test('T1: two flow runs render two flow-run-item details elements', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => MOCK_FLOW_RUNS });
    await loadAgentDetail('agt-1');
    expect(document.querySelectorAll('details.flow-run-item').length).toBe(2);
  });

  test('empty flow runs shows empty-state message', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => [] });
    await loadAgentDetail('agt-1');
    expect(document.querySelector('.empty-state')).not.toBeNull();
    expect(document.getElementById('flow-run-list').textContent).toContain('No runs yet');
  });

  test('HTTP 500 throws (caller handles error display)', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false, status: 500 });
    await expect(loadAgentDetail('agt-1')).rejects.toThrow('Failed to load flow runs');
  });
});
