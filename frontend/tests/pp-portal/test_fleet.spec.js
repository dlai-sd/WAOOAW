import { renderFleetAgentRow, loadFleet } from '../../pp-portal/pages/fleet.js';

const MOCK_AGENT_1 = { id: 'agt-1', name: 'Share Trader', instance_count: 3 };
const MOCK_AGENT_2 = { id: 'agt-2', name: 'Marketing Agent', instance_count: 1 };
const MOCK_SUMMARY = { total: 10, running: 2, completed: 7, failed: 1 };

beforeEach(() => {
  document.body.innerHTML = '<div id="fleet-grid"></div>';
});

describe('renderFleetAgentRow', () => {
  test('T1: renders fleet-row with agent name, instance count, and error rate 10.0%', () => {
    const html = renderFleetAgentRow(MOCK_AGENT_1, MOCK_SUMMARY);
    const div = document.createElement('div');
    div.innerHTML = html;
    expect(div.querySelector('.fleet-row__name').textContent).toContain('Share Trader');
    expect(div.querySelector('.fleet-row__instances').textContent).toContain('3');
    expect(div.querySelector('.fleet-row__error-rate').textContent).toContain('10.0%');
  });

  test('T2: error rate > 10% adds --high class', () => {
    const highErrSummary = { total: 10, running: 0, completed: 7, failed: 2 };
    const html = renderFleetAgentRow(MOCK_AGENT_1, highErrSummary);
    const div = document.createElement('div');
    div.innerHTML = html;
    expect(div.querySelector('.fleet-row__error-rate--high')).not.toBeNull();
  });

  test('T2-safe: error rate <= 10% does NOT add --high class', () => {
    const lowErrSummary = { total: 10, running: 0, completed: 9, failed: 1 };
    const html = renderFleetAgentRow(MOCK_AGENT_1, lowErrSummary);
    const div = document.createElement('div');
    div.innerHTML = html;
    expect(div.querySelector('.fleet-row__error-rate--high')).toBeNull();
  });
});

describe('loadFleet', () => {
  test('T1: two agents render two fleet-row elements', async () => {
    global.fetch
      .mockResolvedValueOnce({ ok: true, json: async () => [MOCK_AGENT_1, MOCK_AGENT_2] })
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_SUMMARY })
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_SUMMARY });

    await loadFleet();
    expect(document.querySelectorAll('.fleet-row').length).toBe(2);
  });

  test('T3: empty agents array shows empty-state message', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => [] });
    await loadFleet();
    expect(document.querySelector('.empty-state')).not.toBeNull();
  });

  test('T4: HTTP 500 from GET /v1/agents throws error (caller handles display)', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false, status: 500 });
    await expect(loadFleet()).rejects.toThrow('Failed to load agents');
  });
});
