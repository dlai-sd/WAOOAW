// frontend/components/AgentCard.js
// CSS vars: --bg-card:#18181b, --color-neon-cyan:#00f2fe,
//           --border-dark:rgba(255,255,255,0.08)
import { renderStatusDot } from './StatusDot.js';
export function renderAgentCard({ id, name, industry, status, specialty,
                                   rating, price, ctaLabel = 'View', ctaHref = '#' }) {
  const initials = name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
  return `
<article class="agent-card" data-agent-id="${id}">
  <div class="agent-card__avatar">${initials}</div>
  <div class="agent-card__info">
    <div class="agent-card__header">
      <h3 class="agent-card__name">${name}</h3>
      ${renderStatusDot(status)}
    </div>
    <span class="agent-card__industry">${industry}</span>
    <p class="agent-card__specialty">${specialty}</p>
    <div class="agent-card__meta">
      <span class="agent-card__rating">⭐ ${rating != null ? rating.toFixed(1) : '—'}</span>
      <span class="agent-card__price">₹${price != null ? price.toLocaleString('en-IN') : '—'}/mo</span>
    </div>
  </div>
  <a href="${ctaHref}" class="btn btn--cyan agent-card__cta">${ctaLabel}</a>
</article>`;
}
