import { Card, Button } from '@fluentui/react-components'

export default function UsageBilling() {
  return (
    <div className="usage-billing-page">
      <div className="page-header">
        <h1>Usage & Billing</h1>
        <div className="plan-info">
          <div>Current Plan: <strong>Starter (Trial)</strong></div>
          <div>Trial Ends: <strong>4 days remaining</strong></div>
          <div>Monthly Cost: <strong>₹24,000</strong></div>
        </div>
      </div>

      <div className="usage-metrics">
        <Card className="usage-card">
          <h3>Query Budget</h3>
          <div className="usage-value">75%</div>
          <div className="status-indicator">🟢 Normal</div>
        </Card>
        <Card className="usage-card">
          <h3>Storage Used</h3>
          <div className="usage-value">2.4 GB</div>
          <div className="status-indicator">🟢 Normal</div>
        </Card>
        <Card className="usage-card">
          <h3>Agents Active</h3>
          <div className="usage-value">2/1</div>
          <div className="status-indicator">🔴 Over Limit</div>
        </Card>
        <Card className="usage-card">
          <h3>Integrations</h3>
          <div className="usage-value">3/3</div>
          <div className="status-indicator">🟡 Full</div>
        </Card>
      </div>

      <Card className="budget-card">
        <h2>Query Budget Consumption (Daily)</h2>
        <div className="budget-item">
          <h4>Agent 1: Content Marketing</h4>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: '75%' }} />
          </div>
          <div>$0.75/$1.00 (75%)</div>
          <div className="budget-alert">Alert: Approaching limit. Increase to $1.50/day?</div>
          <Button appearance="outline">Upgrade</Button>
        </div>
      </Card>

      <Card className="plan-comparison-card">
        <h2>Plan Limits & Upgrade Path</h2>
        <div className="current-plan">
          <h3>Current: Starter Plan (₹12K/agent/month)</h3>
          <ul>
            <li>1 agent (using 2 ⚠️ over limit)</li>
            <li>$1/day query budget per agent</li>
            <li>3 integrations (using 3/3 ✓)</li>
            <li>5 GB storage (using 2.4 GB ✓)</li>
          </ul>
        </div>
        <div className="recommended-plan">
          <h3>Recommended: Pro Plan (₹18K/agent/month)</h3>
          <ul>
            <li>3 agents (room for 1 more)</li>
            <li>$2/day query budget per agent</li>
            <li>Unlimited integrations</li>
            <li>50 GB storage</li>
            <li>Priority support</li>
          </ul>
          <Button appearance="primary">Upgrade to Pro</Button>
          <Button appearance="outline">View Enterprise Plan</Button>
        </div>
      </Card>
    </div>
  )
}
