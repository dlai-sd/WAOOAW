import { renderDeliverableCard } from '../../components/DeliverableCard.js';

describe('renderDeliverableCard', () => {
  test('T3: deliverable with content={order_id:"X"} shows preview with order_id and View full button', () => {
    const d = {
      type: 'trade_signal',
      created_at: new Date('2026-03-08').toISOString(),
      content: { order_id: 'X', symbol: 'BTCUSDT', side: 'BUY' },
    };
    const div = document.createElement('div');
    div.innerHTML = renderDeliverableCard(d);
    expect(div.querySelector('.deliverable-card__preview').textContent).toContain('order_id');
    const btn = div.querySelector('.deliverable-card__expand');
    expect(btn).not.toBeNull();
    expect(btn.textContent).toBe('View full');
    expect(div.querySelector('.deliverable-card__full').hidden).toBe(true);
  });
});
