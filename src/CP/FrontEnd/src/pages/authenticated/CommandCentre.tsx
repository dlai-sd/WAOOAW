import { Card } from '@fluentui/react-components'
import { useNavigate } from 'react-router-dom'

export default function CommandCentre() {
  const navigate = useNavigate()

  const stats = [
    { label: '2 Agents', sublabel: 'Active', value: '🤖' },
    { label: '7/10 Goals', sublabel: 'Completed', value: '🎯' },
    { label: '3 Pending', sublabel: 'Approvals', value: '✅' },
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
      action: 'Needs Approval: Send 3 LinkedIn connection requests',
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

  return (
    <div className="command-centre-page">
      <h1>Command Centre</h1>

      {/* Stats Section */}
      <div className="dashboard-stats">
        {stats.map((stat, idx) => (
          <Card key={idx} className="stat-card">
            <div className="stat-icon">{stat.value}</div>
            <div className="stat-label">{stat.label}</div>
            <div className="stat-sublabel">{stat.sublabel}</div>
          </Card>
        ))}
      </div>

      {/* Activity Feed */}
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

      {/* Quick Actions */}
      <section className="quick-actions">
        <h2>Quick Actions</h2>
        <div className="action-grid">
          <Card className="action-card">
            <h3>🎯 Add New Goal</h3>
            <p>Configure goals for your agents</p>
          </Card>
          <Card className="action-card" onClick={() => navigate('/portal/discover')}>
            <h3>🤖 Hire Another Agent</h3>
            <p>Browse marketplace</p>
          </Card>
          <Card className="action-card">
            <h3>📊 View Deliverables</h3>
            <p>Review what your agents have produced</p>
          </Card>
        </div>
      </section>
    </div>
  )
}
