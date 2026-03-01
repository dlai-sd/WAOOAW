import { Card } from '@fluentui/react-components'

export default function Deliverables() {
  const placeholders = [
    { agent: 'Content Marketing Agent', title: '"5 Ways to Manage Diabetes"', type: 'Article', date: 'Today, 11:47 AM', goal: 'Healthcare Content Q1' },
    { agent: 'Content Marketing Agent', title: 'Fact-Check Report: Medical Claims', type: 'Report', date: 'Today, 11:15 AM', goal: 'Healthcare Content Q1' },
    { agent: 'SDR Agent', title: 'LinkedIn Outreach List (50 prospects)', type: 'Lead List', date: 'Yesterday, 3:20 PM', goal: 'Q1 Pipeline Growth' },
  ]

  return (
    <div className="deliverables-page">
      <div className="page-header" style={{ marginBottom: '24px' }}>
        <h1>Deliverables</h1>
        <p style={{ color: 'var(--colorNeutralForeground2)', marginTop: '4px' }}>
          Everything your agents have produced — filter by agent, date, or goal.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {placeholders.map((item, idx) => (
          <Card key={idx} style={{ padding: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
              <div>
                <div style={{ fontWeight: 700, marginBottom: '4px' }}>{item.title}</div>
                <div style={{ fontSize: '13px', color: 'var(--colorNeutralForeground2)' }}>
                  {item.agent} · {item.type} · {item.date}
                </div>
                <div style={{ fontSize: '13px', color: 'var(--colorNeutralForeground3)', marginTop: '2px' }}>
                  Goal: {item.goal}
                </div>
              </div>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <span style={{ fontSize: '12px', padding: '4px 10px', borderRadius: '12px', background: 'var(--colorNeutralBackground3)', color: 'var(--colorNeutralForeground2)' }}>
                  {item.type}
                </span>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
