import { Card } from '@fluentui/react-components'

export default function Performance() {
  return (
    <div className="performance-page">
      <div className="page-header">
        <h1>Performance Dashboard</h1>
        <select className="date-range">
          <option>Last 7 Days</option>
          <option>Last 30 Days</option>
          <option>Last Quarter</option>
        </select>
      </div>

      <div className="metrics-grid">
        <Card className="metric-card">
          <h3>Goals Progress</h3>
          <div className="metric-value">70%</div>
          <div className="metric-change">↑ +5%</div>
        </Card>
        <Card className="metric-card">
          <h3>Quality Score</h3>
          <div className="metric-value">4.7/5.0</div>
          <div className="metric-change">↑ +0.2</div>
        </Card>
        <Card className="metric-card">
          <h3>Response Time</h3>
          <div className="metric-value">4.2 min</div>
          <div className="metric-change">↓ -1.3min</div>
        </Card>
        <Card className="metric-card">
          <h3>Uptime</h3>
          <div className="metric-value">98.5%</div>
          <div className="metric-change">→ 0%</div>
        </Card>
      </div>

      <Card className="goals-progress-card">
        <h2>Goals Progress (Content Marketing Agent)</h2>
        <div className="goal-item">
          <div className="goal-label">Goal 1: Publish 5 blog posts/week</div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: '60%' }} />
          </div>
          <span>60% (3/5) [On Track]</span>
        </div>
        <div className="goal-item">
          <div className="goal-label">Goal 2: Respond to comments &lt;2 hours</div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: '100%' }} />
          </div>
          <span>100% (8/8) [Done ✓]</span>
        </div>
      </Card>
    </div>
  )
}
