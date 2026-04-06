import { Card } from '@fluentui/react-components'

import { type DeliverablePublishReadiness } from '../services/hiredAgentDeliverables.service'

type DigitalMarketingPublishReadinessCardProps = {
  readiness: DeliverablePublishReadiness
  embedded?: boolean
}

function accentColor(tone: DeliverablePublishReadiness['tone']): string {
  if (tone === 'success') return 'var(--colorPaletteGreenForeground1)'
  if (tone === 'warning') return 'var(--colorPaletteYellowForeground1)'
  if (tone === 'danger') return 'var(--colorPaletteRedForeground1)'
  return 'var(--colorBrandForeground1)'
}

export function DigitalMarketingPublishReadinessCard(props: DigitalMarketingPublishReadinessCardProps) {
  const Container = props.embedded ? 'div' : Card
  const containerProps = props.embedded
    ? { style: { display: 'flex', flexDirection: 'column' as const, gap: '6px' } }
    : { style: { padding: '16px', borderLeft: `3px solid ${accentColor(props.readiness.tone)}` } }

  return (
    <Container {...containerProps}>
      <div style={{ fontWeight: 700, marginBottom: '4px' }}>Publish readiness</div>
      <div style={{ fontWeight: 600, color: accentColor(props.readiness.tone), marginBottom: '6px' }}>
        {props.readiness.label}
      </div>
      <div style={{ fontSize: '13px', color: 'var(--colorNeutralForeground2)' }}>{props.readiness.message}</div>
    </Container>
  )
}

export default DigitalMarketingPublishReadinessCard