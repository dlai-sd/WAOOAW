import { renderApprovalList, updateNavBadge } from '../../pages/approvals.js';

beforeEach(() => {
  document.body.innerHTML = `
    <div id="approval-list"></div>
    <span id="approvals-badge" hidden>0</span>
  `;
});

describe('approvals page', () => {
  test('T3: empty flow-runs array shows empty queue celebration message', async () => {
    await renderApprovalList([]);
    expect(document.querySelector('.empty-state--celebrate')).not.toBeNull();
    expect(document.getElementById('approval-list').textContent).toContain('All caught up');
  });

  test('updateNavBadge: shows badge with count when count > 0', () => {
    updateNavBadge(3);
    const badge = document.getElementById('approvals-badge');
    expect(badge.hidden).toBe(false);
    expect(badge.textContent).toBe('3');
  });

  test('updateNavBadge: hides badge when count = 0', () => {
    updateNavBadge(0);
    expect(document.getElementById('approvals-badge').hidden).toBe(true);
  });
});
