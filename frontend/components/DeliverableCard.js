// frontend/components/DeliverableCard.js
export function renderDeliverableCard(d) {
  const preview = JSON.stringify(d.content).slice(0, 120);
  return `<div class="deliverable-card">
    <span class="deliverable-card__type-badge">${d.type}</span>
    <time class="deliverable-card__time">${new Date(d.created_at).toLocaleString()}</time>
    <p class="deliverable-card__preview">${preview}…</p>
    <button class="deliverable-card__expand"
            onclick="this.nextElementSibling.hidden=!this.nextElementSibling.hidden">View full</button>
    <pre class="deliverable-card__full" hidden>${JSON.stringify(d.content, null, 2)}</pre>
  </div>`;
}
