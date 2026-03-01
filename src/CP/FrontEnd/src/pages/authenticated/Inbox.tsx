import { Card } from '@fluentui/react-components'

export default function Inbox() {
  const messages = [
    {
      agent: 'SDR Agent',
      subject: 'Approval needed: Send 3 LinkedIn connection requests',
      preview: 'I have identified 3 high-fit prospects from your ICP. Requesting approval to send connection requests.',
      time: '11:32 AM',
      type: 'approval',
      unread: true,
    },
    {
      agent: 'Content Marketing Agent',
      subject: 'Trial week 1 summary — 12 pieces published',
      preview: 'Here is a summary of deliverables from your first trial week. Average quality score: 4.7/5.',
      time: 'Yesterday',
      type: 'summary',
      unread: false,
    },
    {
      agent: 'SDR Agent',
      subject: 'Blocker: LinkedIn Sales Navigator access required',
      preview: 'To continue prospecting I need access to LinkedIn Sales Navigator. Please share credentials or invite.',
      time: 'Yesterday',
      type: 'blocker',
      unread: false,
    },
  ]

  const typeColors: Record<string, string> = {
    approval: 'var(--colorPaletteYellowBackground3)',
    summary: 'var(--colorNeutralBackground3)',
    blocker: 'var(--colorPaletteRedBackground1)',
  }

  return (
    <div className="inbox-page">
      <div className="page-header" style={{ marginBottom: '24px' }}>
        <h1>Inbox</h1>
        <p style={{ color: 'var(--colorNeutralForeground2)', marginTop: '4px' }}>
          Agent-initiated messages — approvals, blockers, summaries.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {messages.map((msg, idx) => (
          <Card
            key={idx}
            style={{
              padding: '16px',
              borderLeft: `3px solid ${typeColors[msg.type] || 'transparent'}`,
              cursor: 'pointer',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '4px' }}>
                  {msg.unread && (
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--colorBrandForeground1)', flexShrink: 0 }} />
                  )}
                  <span style={{ fontWeight: msg.unread ? 700 : 500 }}>{msg.subject}</span>
                </div>
                <div style={{ fontSize: '13px', color: 'var(--colorNeutralForeground2)', marginBottom: '4px' }}>
                  {msg.agent}
                </div>
                <div style={{ fontSize: '13px', color: 'var(--colorNeutralForeground3)' }}>
                  {msg.preview}
                </div>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground3)', whiteSpace: 'nowrap' }}>
                {msg.time}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
