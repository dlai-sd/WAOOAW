import { Button, Card } from '@fluentui/react-components'

interface CommandCentreProps {
  onOpenDiscover: () => void
  onOpenBilling: () => void
  onOpenMyAgents: () => void
  onOpenGoals: () => void
}

export default function CommandCentre({ onOpenDiscover, onOpenBilling, onOpenMyAgents, onOpenGoals }: CommandCentreProps) {

  const readinessCards = [
    { label: 'Runtime summary', sublabel: 'Loads after your agents begin executing work', value: '⏳' },
    { label: 'Billing proof', sublabel: 'Appears when subscriptions, invoices, or receipts exist', value: '🧾' },
    { label: 'Approvals', sublabel: 'Only appears when your decision is actually required', value: '✅' },
    { label: 'Profile control', sublabel: 'Confirm or update account identity before scaling hires', value: '👤' },
  ]

  const priorities = [
    'Open My Agents to confirm which hires are actually configured and active.',
    'Review billing only after a live subscription or invoice record exists.',
    'Use Goals to define the next business outcome instead of assuming runtime defaults.',
  ]

  return (
    <div className="dashboard-page">
      <div className="dashboard-stats">
        {readinessCards.map((stat, idx) => (
          <Card key={idx} className="stat-card">
            <div className="stat-icon">{stat.value}</div>
            <div className="stat-label">{stat.label}</div>
            <div className="stat-sublabel">{stat.sublabel}</div>
          </Card>
        ))}
      </div>

      <div className="command-centre-grid">
        <Card className="command-centre-panel">
          <div className="section-header">
            <h2>Today&#39;s Flight Plan</h2>
            <span className="live-indicator">Top 3 priorities</span>
          </div>
          <div className="command-centre-checklist">
            {priorities.map((item) => (
              <div key={item} className="command-centre-checklist-item">
                <span>•</span>
                <span>{item}</span>
              </div>
            ))}
          </div>
          <div className="command-centre-actions">
            <Button appearance="primary" onClick={onOpenMyAgents}>Open My Agents</Button>
            <Button appearance="secondary" onClick={onOpenBilling}>Review Spend</Button>
          </div>
        </Card>

        <Card className="command-centre-panel command-centre-panel--accent">
          <div className="section-header">
            <h2>Runtime Truth</h2>
            <span className="live-indicator">Action-needed state</span>
          </div>
          <div className="command-centre-pulse-grid">
            <div>
              <div className="command-centre-pulse-value">0</div>
              <div className="command-centre-pulse-label">Live KPIs shown without a fetch</div>
            </div>
            <div>
              <div className="command-centre-pulse-value">1</div>
              <div className="command-centre-pulse-label">Place to confirm billing truth</div>
            </div>
            <div>
              <div className="command-centre-pulse-value">3</div>
              <div className="command-centre-pulse-label">Next actions before trust breaks</div>
            </div>
          </div>
          <p className="command-centre-pulse-body">
            This shell does not have a live runtime feed yet. Use My Agents, Billing, and Profile to confirm real state instead of reading fake counters here.
          </p>
        </Card>
      </div>

      <section className="activity-section">
        <div className="section-header">
          <h2>Agent Activity Feed</h2>
          <span className="live-indicator">Hydrates after runtime starts</span>
        </div>
        <div className="activity-feed">
          <Card className="activity-card">
            <div className="activity-agent">No live agent activity yet</div>
            <div className="activity-action">Once a hired agent begins running, the latest output and approvals will appear here.</div>
            <div className="activity-meta">What to do next: finish setup in My Agents or hire your first agent from Discover.</div>
          </Card>
        </div>
      </section>

      <section className="quick-actions">
        <h2>Quick Actions</h2>
        <div className="action-grid">
          <Card className="action-card" onClick={onOpenGoals}>
            <h3>🎯 Add New Goal</h3>
            <p>Configure goals for your agents</p>
          </Card>
          <Card className="action-card" onClick={onOpenDiscover}>
            <h3>🤖 Hire Another Agent</h3>
            <p>Browse the marketplace with outcomes first</p>
          </Card>
          <Card className="action-card" onClick={onOpenBilling}>
            <h3>💰 Review Spend</h3>
            <p>Understand billing, receipts, and what changed</p>
          </Card>
        </div>
      </section>
    </div>
  )
}
