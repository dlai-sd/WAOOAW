import { Badge, Card } from '@fluentui/react-components'
import type { TradingSetupReadiness } from '../services/tradingSetup.service'

interface Props {
  readiness: TradingSetupReadiness
  onConfigureCta?: () => void
}

const CHECK_ITEMS: Array<{ key: keyof TradingSetupReadiness; label: string }> = [
  { key: 'has_credentials', label: 'Credentials entered' },
  { key: 'credentials_valid', label: 'Credentials validated' },
  { key: 'has_instrument', label: 'Instrument selected' },
  { key: 'has_rsi_period', label: 'RSI period set' },
  { key: 'has_risk_limits', label: 'Risk limits set' },
]

export function TradingReadinessCard({ readiness, onConfigureCta }: Props) {
  const allReady = readiness.configured
  return (
    <Card style={{ background: '#18181b', border: `1px solid ${allReady ? '#10b98155' : '#27272a'}`,
      borderRadius: 12, padding: 16, marginBottom: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <span style={{ color: '#f4f4f5', fontWeight: 600, fontSize: 14 }}>Configuration Readiness</span>
        {allReady
          ? <Badge appearance="filled" color="success">✅ Ready to trade</Badge>
          : <button onClick={onConfigureCta} style={{ color: '#00f2fe', background: 'none',
              border: '1px solid #00f2fe55', borderRadius: 6, padding: '4px 10px',
              fontSize: 12, cursor: 'pointer' }}>Complete setup →</button>
        }
      </div>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {CHECK_ITEMS.map(({ key, label }) => (
          <Badge
            key={key}
            appearance="tint"
            color={readiness[key] ? 'success' : 'danger'}
            size="small"
            data-testid={`readiness-${key}`}
          >
            {readiness[key] ? '✓' : '✗'} {label}
          </Badge>
        ))}
      </div>
    </Card>
  )
}
