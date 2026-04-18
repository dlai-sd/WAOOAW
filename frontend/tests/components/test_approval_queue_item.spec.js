import { renderApprovalQueueItem, approveFlowRun, rejectFlowRun }
  from '../../components/ApprovalQueueItem.js';

describe('renderApprovalQueueItem', () => {
  test('T1: per_platform_variants with linkedin shows platform name in preview', () => {
    const deliverable = { content: { per_platform_variants: { linkedin: { post_text: 'hello' } } } };
    const div = document.createElement('div');
    div.innerHTML = renderApprovalQueueItem({ id: 'run-1' }, deliverable, 'Marketing Agent');
    expect(div.querySelector('.approval-item__preview').textContent).toContain('linkedin');
  });

  test('T2: clicking Approve calls API, disables button, removes item from DOM', async () => {
    document.body.innerHTML = `
      <div id="approval-list">
        <div class="approval-item" data-flow-run-id="run-1">
          <button class="btn btn--cyan" id="approve-btn">Approve</button>
          <button class="btn btn--red">Reject</button>
        </div>
      </div>
    `;
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
