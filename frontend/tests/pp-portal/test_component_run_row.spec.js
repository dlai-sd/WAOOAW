import { renderComponentRunRow } from '../../pp-portal/components/ComponentRunRow.js';

describe('renderComponentRunRow', () => {
  test('T3: status=failed renders cr-row--error class and shows error message', () => {
    const cr = { step_name: 'DeltaExchangePump', status: 'failed', duration_ms: 300, error_message: 'Timeout after 30s' };
    const div = document.createElement('div');
    div.innerHTML = renderComponentRunRow(cr);
    expect(div.querySelector('.cr-row--error')).not.toBeNull();
    expect(div.querySelector('.cr-row__error')).not.toBeNull();
    expect(div.querySelector('.cr-row__error').textContent).toContain('Timeout after 30s');
  });

  test('T4: error_message longer than 80 chars is truncated with ellipsis', () => {
    const longError = 'A'.repeat(100);
    const cr = { step_name: 'Pump', status: 'failed', duration_ms: 100, error_message: longError };
    const div = document.createElement('div');
    div.innerHTML = renderComponentRunRow(cr);
    const errSpan = div.querySelector('.cr-row__error');
    expect(errSpan).not.toBeNull();
    expect(errSpan.textContent.endsWith('…')).toBe(true);
    expect(errSpan.textContent.length).toBeLessThan(longError.length);
  });

  test('renders success icon for completed status', () => {
    const cr = { step_name: 'Processor', status: 'completed', duration_ms: 120 };
    const div = document.createElement('div');
    div.innerHTML = renderComponentRunRow(cr);
    expect(div.querySelector('.cr-row--success')).not.toBeNull();
    expect(div.querySelector('.cr-row__icon').textContent).toBe('✓');
  });

  test('renders duration when provided', () => {
    const cr = { step_name: 'Publisher', status: 'completed', duration_ms: 456 };
    const div = document.createElement('div');
    div.innerHTML = renderComponentRunRow(cr);
    expect(div.querySelector('.cr-row__dur').textContent).toContain('456ms');
  });

  test('does not render duration element when duration_ms is absent', () => {
    const cr = { step_name: 'Pending', status: 'pending' };
    const div = document.createElement('div');
    div.innerHTML = renderComponentRunRow(cr);
    expect(div.querySelector('.cr-row__dur')).toBeNull();
  });
});
