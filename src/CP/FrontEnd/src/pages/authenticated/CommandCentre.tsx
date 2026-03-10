import { Button, Card } from '@fluentui/react-components'

interface CommandCentreProps {
  onOpenDiscover: () => void
  onOpenBilling: () => void
  onOpenMyAgents: () => void
  onOpenGoals: () => void
}

export default function CommandCentre({ onOpenDiscover, onOpenBilling, onOpenMyAgents, onOpenGoals }: CommandCentreProps) {

  const stats = [
    { label: '2 Agents', sublabel: 'Active', value: '🤖' },
    { label: '7/10 Goals', sublabel: 'Completed', value: '🎯' },
    { label: '3 Messages', sublabel: 'In Inbox', value: '📬' },
    { label: '₹24K/mo', sublabel: 'Current', value: '💰' },
  ]

  const activityFeed = [
    {
      time: '11:47 AM',
      agent: 'Content Marketing Agent',
      action: 'Published: "5 Ways to Manage Diabetes"',
      quality: 4.8,
      budget: 0.42
    },
    {
      time: '11:32 AM',
      agent: 'SDR Agent',
      action: 'Needs Review: Send 3 LinkedIn connection requests',
      status: 'pending'
    },
    {
      time: '11:15 AM',
      agent: 'Content Marketing Agent',
      action: 'Executed: Fact-Check Medical Claims (8 sources)',
      status: 'passed',
      duration: '3.2 min'
    }
  ]

  const priorities = [
    'Approve the SDR connection request so outbound work resumes.',
    'Review today\'s spend trend before the next billing cycle closes.',
    'Add one more growth goal for your content operator.',
  ]

  return (
    <div className="dashboard-page">
      <div className="dashboard-stats">
        {stats.map((stat, idx) => (
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
            <h2>Business Pulse</h2>
            <span className="live-indicator">Updated 2m ago</span>
          </div>
          <div className="command-centre-pulse-grid">
            <div>
              <div className="command-centre-pulse-value">98%</div>
              <div className="command-centre-pulse-label">Goal adherence</div>
            </div>
            <div>
              <div className="command-centre-pulse-value">₹6.4K</div>
              <div className="command-centre-pulse-label">Spend this week</div>
            </div>
            <div>
              <div className="command-centre-pulse-value">1</div>
              <div className="command-centre-pulse-label">Blocked workflow</div>
            </div>
          </div>
          <p className="command-centre-pulse-body">
            Your strongest momentum is in content publishing. Sales outreach is waiting on one approval, so that is the highest leverage unblock.
          </p>
        </Card>
      </div>

      <section className="activity-section">
        <div className="section-header">
          <h2>Agent Activity Feed</h2>
          <span className="live-indicator">🔄 Live Feed</span>
        </div>
        <div className="activity-feed">
          {activityFeed.map((activity, idx) => (
            <Card key={idx} className="activity-card">
              <div className="activity-time">{activity.time}</div>
              <div className="activity-agent">{activity.agent}</div>
              <div className="activity-action">{activity.action}</div>
              {activity.quality && (
                <div className="activity-meta">
                  Quality: ⭐ {activity.quality} | Budget: ${activity.budget}
                </div>
              )}
              {activity.status && (
                <div className="activity-status">{activity.status}</div>
              )}
            </Card>
          ))}
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
