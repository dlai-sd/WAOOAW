import { renderAgentCard } from '../../components/AgentCard.js';
import { renderStatusDot }  from '../../components/StatusDot.js';

const BASE = {
  id: 'agent-1', name: 'Marketing Manager', industry: 'marketing',
  status: 'running', specialty: 'B2B content strategy',
  rating: 4.8, price: 12000,
  ctaLabel: 'Start 7-day trial', ctaHref: '/hire/agent-1',
};

describe('renderAgentCard', () => {
  test('T1: renders agent name, status dot, and CTA link', () => {
    const div = document.createElement('div');
    div.innerHTML = renderAgentCard(BASE);
    expect(div.querySelector('.agent-card__name').textContent).toBe('Marketing Manager');
    expect(div.querySelector('.status-dot')).not.toBeNull();
    const cta = div.querySelector('.agent-card__cta');
    expect(cta).not.toBeNull();
    expect(cta.getAttribute('href')).toBe('/hire/agent-1');
    expect(cta.textContent.trim()).toBe('Start 7-day trial');
  });

  test('T2: status=failed maps StatusDot color to --status-red', () => {
    const div = document.createElement('div');
    div.innerHTML = renderAgentCard({ ...BASE, status: 'failed' });
    const dot = div.querySelector('.status-dot');
    expect(dot.getAttribute('style')).toContain('--status-red');
  });

  test('T3: missing optional props renders without exception and shows em-dash', () => {
    expect(() => {
      const div = document.createElement('div');
      div.innerHTML = renderAgentCard({ ...BASE, rating: undefined, price: undefined });
      expect(div.querySelector('.agent-card__rating').textContent).toContain('—');
      expect(div.querySelector('.agent-card__price').textContent).toContain('—');
    }).not.toThrow();
  });
});

describe('renderStatusDot', () => {
  test('running status renders green color', () => {
    const html = renderStatusDot('running');
    expect(html).toContain('--status-green');
    expect(html).toContain('aria-label="Running"');
  });

  test('unknown status falls back to gray', () => {
    const html = renderStatusDot('unknown_status');
    expect(html).toContain('--status-gray');
  });
});
