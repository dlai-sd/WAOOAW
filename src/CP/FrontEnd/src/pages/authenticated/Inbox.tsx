import { Button, Card, Spinner } from '@fluentui/react-components'

export type CustomerInboxItem = {
  deliverableId: string
  hiredInstanceId: string
  agentLabel: string
  title: string
  preview: string
  reviewStatus: string
  approvalId?: string | null
  reviewNotes?: string | null
  createdAt?: string | null
  updatedAt?: string | null
  channelStatusLabel?: string | null
  publishReadinessLabel?: string | null
  publishReadinessGuidance?: string | null
}

type InboxProps = {
  items?: CustomerInboxItem[]
  loading?: boolean
  error?: string | null
  onOpenMyAgents?: (hiredInstanceId?: string) => void
}

function getStatusMeta(reviewStatus: string): {
  label: string
  accent: string
  surface: string
  guidance: string
} {
  const normalized = String(reviewStatus || '').trim().toLowerCase()

  if (normalized === 'approved') {
    return {
      label: 'Approved',
      accent: 'var(--colorPaletteGreenForeground1)',
      surface: 'var(--colorPaletteGreenBackground1)',
      guidance: 'You already approved this deliverable, so the agent can continue with the next step.',
    }
  }

  if (normalized === 'rejected') {
    return {
      label: 'Not approved',
      accent: 'var(--colorPaletteRedForeground1)',
      surface: 'var(--colorPaletteRedBackground1)',
      guidance: 'You rejected this deliverable. It stays visible so you can track what needs revision.',
    }
  }

  return {
    label: 'Needs your approval',
    accent: 'var(--colorPaletteYellowForeground1)',
    surface: 'var(--colorPaletteYellowBackground1)',
    guidance: 'Review this deliverable before the agent or operator moves forward.',
  }
}

export default function Inbox(props: InboxProps) {
  const items = props.items || []
  const loading = Boolean(props.loading)
  const error = props.error || null

  const counts = items.reduce(
    (acc, item) => {
      const normalized = String(item.reviewStatus || '').trim().toLowerCase()
      if (normalized === 'approved') acc.approved += 1
      else if (normalized === 'rejected') acc.rejected += 1
      else acc.pending += 1
      return acc
    },
    { pending: 0, approved: 0, rejected: 0 }
  )

  return (
    <div className="inbox-page">
      <div className="page-header" style={{ marginBottom: '24px' }}>
        <h1>Inbox</h1>
        <p style={{ color: 'var(--colorNeutralForeground2)', marginTop: '4px' }}>
          Customer-readable approval outcomes and deliverable states across your hired agents.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', marginBottom: '16px' }}>
        <Card style={{ padding: '16px' }}>
          <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground3)', marginBottom: '6px' }}>Awaiting your decision</div>
          <div style={{ fontSize: '28px', fontWeight: 700 }}>{counts.pending}</div>
        </Card>
        <Card style={{ padding: '16px' }}>
          <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground3)', marginBottom: '6px' }}>Approved and visible</div>
          <div style={{ fontSize: '28px', fontWeight: 700 }}>{counts.approved}</div>
        </Card>
        <Card style={{ padding: '16px' }}>
          <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground3)', marginBottom: '6px' }}>Rejected and tracked</div>
          <div style={{ fontSize: '28px', fontWeight: 700 }}>{counts.rejected}</div>
        </Card>
      </div>

      {loading ? (
        <Card style={{ padding: '20px', marginBottom: '16px' }}>
          <Spinner label="Loading deliverable states..." />
        </Card>
      ) : null}

      {error ? (
        <Card style={{ padding: '16px', marginBottom: '16px', borderLeft: '3px solid var(--colorPaletteRedForeground1)' }}>
          <div style={{ fontWeight: 700, marginBottom: '4px' }}>Unable to load the latest deliverable states</div>
          <div style={{ color: 'var(--colorNeutralForeground2)' }}>{error}</div>
        </Card>
      ) : null}

      {!loading && items.length === 0 ? (
        <Card style={{ padding: '20px' }}>
          <div style={{ fontWeight: 700, marginBottom: '6px' }}>No deliverable decisions yet</div>
          <div style={{ color: 'var(--colorNeutralForeground2)' }}>
            When your agents create work that needs review, approved work, or rejected revisions, it will appear here.
          </div>
        </Card>
      ) : null}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {items.map((item) => {
          const status = getStatusMeta(item.reviewStatus)
          const timestamp = item.updatedAt || item.createdAt || null
          return (
            <Card
              key={item.deliverableId}
              style={{
                padding: '16px',
                borderLeft: `3px solid ${status.accent}`,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px', flexWrap: 'wrap' }}>
                <div style={{ flex: 1, minWidth: '260px' }}>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '6px', flexWrap: 'wrap' }}>
                    <span
                      style={{
                        fontSize: '12px',
                        padding: '4px 10px',
                        borderRadius: '999px',
                        background: status.surface,
                        color: status.accent,
                        fontWeight: 700,
                      }}
                    >
                      {status.label}
                    </span>
                    <span style={{ fontWeight: 700 }}>{item.title}</span>
                  </div>
                  <div style={{ fontSize: '13px', color: 'var(--colorNeutralForeground2)', marginBottom: '6px' }}>
                    {item.agentLabel}
                    {item.approvalId ? ` • Approval ${item.approvalId}` : ''}
                  </div>
                  <div style={{ fontSize: '13px', color: 'var(--colorNeutralForeground3)', marginBottom: '8px' }}>
                    {item.preview}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground2)' }}>{status.guidance}</div>
                  {item.channelStatusLabel ? (
                    <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground2)', marginTop: '8px' }}>
                      Channel: {item.channelStatusLabel}
                    </div>
                  ) : null}
                  {item.publishReadinessLabel ? (
                    <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground2)', marginTop: '4px' }}>
                      Publish readiness: {item.publishReadinessLabel}
                      {item.publishReadinessGuidance ? ` — ${item.publishReadinessGuidance}` : ''}
                    </div>
                  ) : null}
                  {item.reviewNotes ? (
                    <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground2)', marginTop: '8px' }}>
                      Latest note: {item.reviewNotes}
                    </div>
                  ) : null}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '10px' }}>
                  <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground3)', whiteSpace: 'nowrap' }}>
                    {timestamp ? new Date(timestamp).toLocaleString() : 'Recently updated'}
                  </div>
                  <Button appearance="secondary" onClick={() => props.onOpenMyAgents?.(item.hiredInstanceId)}>
                    Open My Agents
                  </Button>
                </div>
              </div>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
