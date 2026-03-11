import { Card, Spinner } from '@fluentui/react-components'

import { type PlatformConnectionSummary } from '../services/platformConnections.service'

type DigitalMarketingChannelStatusCardProps = {
  summary: PlatformConnectionSummary | null
  loading?: boolean
  error?: string | null
}

function accentColor(tone: PlatformConnectionSummary['tone'] | 'danger'): string {
  if (tone === 'success') return 'var(--colorPaletteGreenForeground1)'
  if (tone === 'warning') return 'var(--colorPaletteYellowForeground1)'
  if (tone === 'danger') return 'var(--colorPaletteRedForeground1)'
  return 'var(--colorBrandForeground1)'
}

export function DigitalMarketingChannelStatusCard(props: DigitalMarketingChannelStatusCardProps) {
  if (props.loading) {
    return (
      <Card style={{ padding: '16px' }}>
        <Spinner label="Loading YouTube channel state..." />
      </Card>
    )
  }

  if (props.error) {
    return (
      <Card style={{ padding: '16px', borderLeft: '3px solid var(--colorPaletteRedForeground1)' }}>
        <div style={{ fontWeight: 700, marginBottom: '4px' }}>YouTube channel status unavailable</div>
        <div style={{ fontSize: '13px', color: 'var(--colorNeutralForeground2)' }}>{props.error}</div>
      </Card>
    )
  }

  const summary = props.summary
  if (!summary) return null

  return (
    <Card style={{ padding: '16px', borderLeft: `3px solid ${accentColor(summary.tone)}` }}>
      <div style={{ fontWeight: 700, marginBottom: '4px' }}>YouTube channel status</div>
      <div style={{ fontWeight: 600, color: accentColor(summary.tone), marginBottom: '6px' }}>{summary.label}</div>
      <div style={{ fontSize: '13px', color: 'var(--colorNeutralForeground2)' }}>{summary.message}</div>
    </Card>
  )
}

export default DigitalMarketingChannelStatusCard