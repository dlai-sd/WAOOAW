import { renderDlqItem, loadDlq, requeueTask, skipTask, updateNavBadge } from '../../pp-portal/pages/dlq.js';

const MOCK_TASKS = [
  { id: 'task-aabbccdd', agent_name: 'Share Trader', step_name: 'DeltaExchangePump', failure_count: 3, last_error: 'Connection refused' },
  { id: 'task-eeff0011', agent_name: 'Marketing Agent', step_name: 'ContentProcessor', failure_count: 1, last_error: null },
];

beforeEach(() => {
  document.body.innerHTML = `
    <div id="dlq-list"></div>
    <span id="dlq-badge" hidden>0</span>
  `;
});

describe('renderDlqItem', () => {
  test('renders dlq-item with agent name, step name, failure count', () => {
    const html = renderDlqItem(MOCK_TASKS[0]);
    const div = document.createElement('div');
    div.innerHTML = html;
    expect(div.querySelector('.dlq-item__agent').textContent).toBe('Share Trader');
    expect(div.querySelector('.dlq-item__step').textContent).toBe('DeltaExchangePump');
    expect(div.querySelector('.dlq-item__failures').textContent).toContain('3×');
  });

  test('shows "No error detail" when last_error is null', () => {
    const html = renderDlqItem(MOCK_TASKS[1]);
    const div = document.createElement('div');
    div.innerHTML = html;
    expect(div.querySelector('.dlq-item__error').textContent).toContain('No error detail');
  });
});

describe('loadDlq', () => {
  test('T1: 2 tasks render two dlq-item elements', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => MOCK_TASKS });
    await loadDlq();
    expect(document.querySelectorAll('.dlq-item').length).toBe(2);
  });

  test('T4: empty tasks array shows "Queue is clear" celebration message', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => [] });
    await loadDlq();
    expect(document.querySelector('.empty-state--celebrate')).not.toBeNull();
    expect(document.getElementById('dlq-list').textContent).toContain('Queue is clear');
  });

  test('T5: HTTP 500 throws (caller renders error message)', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false, status: 500 });
    await expect(loadDlq()).rejects.toThrow('Failed to load DLQ');
  });
});

describe('requeueTask', () => {
  test('T2: successful requeue disables buttons and removes item from DOM', async () => {
    document.body.innerHTML = `
      <div id="dlq-list">
        <div class="dlq-item" data-task-id="task-aabbccdd">
          <button id="requeue-btn" class="btn btn--cyan">Requeue</button>
          <button id="skip-btn" class="btn btn--red">Skip</button>
        </div>
      </div>
    `;
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) });
    const btn = document.getElementById('requeue-btn');
    await requeueTask('task-aabbccdd', btn);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/v1/dlq/task-aabbccdd/requeue'),
      expect.objectContaining({ method: 'POST' })
    );
    expect(document.querySelector('[data-task-id="task-aabbccdd"]')).toBeNull();
  });
});

describe('skipTask', () => {
  test('T3: confirm=false does NOT call API or remove item', async () => {
    document.body.innerHTML = '<div class="dlq-item" data-task-id="task-eeff0011"></div>';
    global.confirm.mockReturnValueOnce(false);
    await skipTask('task-eeff0011');
    expect(global.fetch).not.toHaveBeenCalled();
    expect(document.querySelector('[data-task-id="task-eeff0011"]')).not.toBeNull();
  });

  test('skip with confirm=true calls API and removes item', async () => {
    document.body.innerHTML = '<div class="dlq-item" data-task-id="task-eeff0011"></div>';
    global.confirm.mockReturnValueOnce(true);
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) });
    await skipTask('task-eeff0011');
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/v1/dlq/task-eeff0011/skip'),
      expect.objectContaining({ method: 'POST' })
    );
    expect(document.querySelector('[data-task-id="task-eeff0011"]')).toBeNull();
  });
});

describe('updateNavBadge', () => {
  test('shows badge with count > 0', () => {
    updateNavBadge(5);
    const badge = document.getElementById('dlq-badge');
    expect(badge.hidden).toBe(false);
    expect(badge.textContent).toBe('5');
  });

  test('hides badge when count = 0', () => {
    updateNavBadge(0);
    expect(document.getElementById('dlq-badge').hidden).toBe(true);
  });
});
