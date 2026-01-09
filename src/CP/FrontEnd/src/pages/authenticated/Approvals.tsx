import { Card, Button } from '@fluentui/react-components'

interface ApprovalRequest {
  id: string
  agent: string
  action: string
  context: string
  rationale: string
  risk: 'low' | 'medium' | 'high'
  cost: number
  timeoutHours: number
  waitingMinutes: number
}

export default function Approvals() {
  const approvals: ApprovalRequest[] = [
    {
      id: '1',
      agent: 'SDR Agent',
      action: 'Send 3 LinkedIn connection requests',
      context: 'Target: SaaS Decision Makers at Series B companies',
      rationale: 'Prospects match ICP: 100+ employees, recent funding, using competitor products',
      risk: 'low',
      cost: 0.03,
      timeoutHours: 9,
      waitingMinutes: 15
    },
    {
      id: '2',
      agent: 'Content Marketing Agent',
      action: 'Publish blog post "5 Ways to Manage Type 2 Diabetes"',
      context: 'Public content, medical topic (HIPAA compliant)',
      rationale: 'Quality Score: ⭐ 4.8 | Fact-Check: ✓ 8 sources validated',
      risk: 'low',
      cost: 0.12,
      timeoutHours: 23,
      waitingMinutes: 42
    }
  ]

  return (
    <div className="approvals-page">
      <div className="page-header">
        <h1>Pending Approvals ({approvals.length})</h1>
        <div className="filter-controls">
          <select className="filter-select">
            <option>All</option>
            <option>Urgent</option>
            <option>Low Risk</option>
          </select>
          <select className="sort-select">
            <option>Newest First</option>
            <option>Oldest First</option>
            <option>By Risk</option>
          </select>
        </div>
      </div>

      <div className="approvals-list">
        {approvals.map((approval) => (
          <Card key={approval.id} className="approval-card">
            <div className="approval-header">
              <div className="approval-agent">{approval.agent}</div>
              <div className="approval-wait">
                {approval.waitingMinutes < 30 ? '🟡' : '🔴'} 
                Waiting {approval.waitingMinutes} min
              </div>
            </div>

            <div className="approval-body">
              <h3>Action Requested:</h3>
              <p className="approval-action">{approval.action}</p>

              <h4>Context:</h4>
              <p>{approval.context}</p>

              <h4>Agent Rationale:</h4>
              <p>{approval.rationale}</p>

              <div className="approval-meta">
                <span>Risk Level: <strong>{approval.risk.toUpperCase()}</strong></span>
                <span> | </span>
                <span>Estimated Cost: ${approval.cost.toFixed(2)}</span>
                <span> | </span>
                <span>Timeout: {approval.timeoutHours}h remaining</span>
              </div>
            </div>

            <div className="approval-actions">
              <Button appearance="primary" style={{ backgroundColor: '#10b981' }}>
                ✅ APPROVE
              </Button>
              <Button appearance="primary" style={{ backgroundColor: '#ef4444' }}>
                ❌ DENY
              </Button>
              <Button appearance="outline" style={{ borderColor: '#f59e0b' }}>
                ⏸ DEFER
              </Button>
              <Button appearance="subtle">
                ⚠️ ESCALATE
              </Button>
              <Button appearance="subtle">
                View Full Details
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
