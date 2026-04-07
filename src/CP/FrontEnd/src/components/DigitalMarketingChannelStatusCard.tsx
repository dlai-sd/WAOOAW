import { Badge, Button, Card, Spinner } from '@fluentui/react-components'

import { type PlatformConnectionSummary } from '../services/platformConnections.service'
import { type ValidateYouTubeConnectionResponse, type YouTubeConnection } from '../services/youtubeConnections.service'

type DigitalMarketingChannelStatusCardProps = {
  summary: PlatformConnectionSummary | null
  loading?: boolean
  error?: string | null
  embedded?: boolean
  credential?: YouTubeConnection | null
  validationResult?: ValidateYouTubeConnectionResponse | null
  actionMessage?: string | null
  connectionLoading?: boolean
  validationLoading?: boolean
  persistLoading?: boolean
  onConnectOrReconnect?: (() => void) | null
  onTestConnection?: (() => void) | null
  onPersistConnection?: (() => void) | null
  canPersistConnection?: boolean
}

function accentColor(tone: PlatformConnectionSummary['tone'] | 'danger'): string {
  if (tone === 'success') return 'var(--colorPaletteGreenForeground1)'
  if (tone === 'warning') return 'var(--colorPaletteYellowForeground1)'
  if (tone === 'danger') return 'var(--colorPaletteRedForeground1)'
  return 'var(--colorBrandForeground1)'
}

export function DigitalMarketingChannelStatusCard(props: DigitalMarketingChannelStatusCardProps) {
  const Container = props.embedded ? 'div' : Card
  const containerProps = props.embedded
    ? { style: { display: 'flex', flexDirection: 'column' as const, gap: '12px' } }
    : { style: { padding: '16px', borderLeft: `3px solid ${accentColor(props.summary?.tone || 'danger')}` } }

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

  const credential = props.credential
  const hasSavedCredential = Boolean(credential?.id)
  const isAttached = Boolean(summary.connection)
  const channelReady = String(props.validationResult?.connection_status || credential?.connection_status || '').trim().toLowerCase() === 'connected'
  const shouldShowPersist = Boolean(props.canPersistConnection && hasSavedCredential && !isAttached && channelReady)
  const connectLabel = hasSavedCredential ? 'Reconnect with Google' : 'Connect YouTube'
  const accountOnly = String(credential?.connection_status || '').trim().toLowerCase() === 'connected_no_channel'

  return (
    <Container {...containerProps}>
      <div>
        <div style={{ fontWeight: 700, marginBottom: '4px' }}>YouTube channel status</div>
        <div style={{ fontWeight: 600, color: accentColor(summary.tone), marginBottom: '6px' }}>{summary.label}</div>
        <div style={{ fontSize: '13px', color: 'var(--colorNeutralForeground2)' }}>{summary.message}</div>
      </div>

      {credential ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '12px' }}>
          <div>
            <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground3)', marginBottom: '4px' }}>{accountOnly ? 'Google account' : 'Channel'}</div>
            <div style={{ fontWeight: 600 }}>{credential.display_name || (accountOnly ? 'Saved Google account' : 'Saved YouTube channel')}</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground3)', marginBottom: '4px' }}>Credential state</div>
            <div style={{ fontWeight: 600 }}>{String(credential.connection_status || 'unknown').replace(/_/g, ' ')}</div>
          </div>
          {credential.last_verified_at ? (
            <div>
              <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground3)', marginBottom: '4px' }}>Last verified</div>
              <div style={{ fontWeight: 600 }}>{new Date(credential.last_verified_at).toLocaleString()}</div>
            </div>
          ) : null}
        </div>
      ) : null}

      {props.validationResult ? (
        <div data-testid="youtube-validation-metrics" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '12px' }}>
          <div>
            <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground3)' }}>Videos</div>
            <div style={{ fontWeight: 700 }}>{props.validationResult.total_video_count}</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground3)' }}>Shorts</div>
            <div style={{ fontWeight: 700 }}>{props.validationResult.recent_short_count}</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground3)' }}>Long videos</div>
            <div style={{ fontWeight: 700 }}>{props.validationResult.recent_long_video_count}</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground3)' }}>Subscribers</div>
            <div style={{ fontWeight: 700 }}>{props.validationResult.subscriber_count}</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground3)' }}>Views</div>
            <div style={{ fontWeight: 700 }}>{props.validationResult.view_count}</div>
          </div>
        </div>
      ) : null}

      {props.validationResult?.recent_uploads && props.validationResult.recent_uploads.length > 0 ? (
        <div data-testid="youtube-recent-uploads" style={{ marginTop: '8px' }}>
          <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground3)', marginBottom: '6px', fontWeight: 600 }}>Recent uploads (proof)</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {props.validationResult.recent_uploads.map((upload) => (
              <div
                key={upload.video_id}
                style={{
                  padding: '8px',
                  borderRadius: '4px',
                  background: 'var(--colorNeutralBackground1Hover)',
                  fontSize: '13px',
                }}
              >
                <div style={{ fontWeight: 600, marginBottom: '2px' }}>{upload.title}</div>
                <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground3)' }}>
                  {new Date(upload.published_at).toLocaleDateString()} · {Math.floor(upload.duration_seconds / 60)}:{String(upload.duration_seconds % 60).padStart(2, '0')}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {props.validationResult?.next_action_hint ? (
        <div data-testid="youtube-next-action-hint" style={{ marginTop: '8px' }}>
          {props.validationResult.next_action_hint === 'reconnect_required' ? (
            <div style={{ padding: '8px', borderRadius: '4px', background: 'var(--colorPaletteRedBackground1)', border: '1px solid var(--colorPaletteRedBorder1)', fontSize: '13px' }}>
              ⚠️ Token expired — reconnect with Google to restore access
            </div>
          ) : props.validationResult.next_action_hint === 'token_expiring_soon' ? (
            <div style={{ padding: '8px', borderRadius: '4px', background: 'var(--colorPaletteYellowBackground1)', border: '1px solid var(--colorPaletteYellowBorder1)', fontSize: '13px' }}>
              ⏰ Token expires soon — consider reconnecting to avoid disruption
            </div>
          ) : props.validationResult.next_action_hint === 'connected_ready' ? (
            <div style={{ padding: '8px', borderRadius: '4px', background: 'var(--colorPaletteGreenBackground1)', border: '1px solid var(--colorPaletteGreenBorder1)', fontSize: '13px' }}>
              ✅ Connected and ready — your DMA can access this channel
            </div>
          ) : null}
        </div>
      ) : null}

      {props.actionMessage ? (
        <div style={{ fontSize: '13px', color: 'var(--colorNeutralForeground2)' }}>{props.actionMessage}</div>
      ) : null}

      {accountOnly ? (
        <div style={{ fontSize: '13px', color: 'var(--colorNeutralForeground2)' }}>
          No YouTube channel exists on this account yet. Create a channel named {credential?.suggested_channel_name || 'Empower'}, then test the connection again.
          {credential?.create_channel_url ? (
            <>
              {' '}
              <a href={credential.create_channel_url} target="_blank" rel="noreferrer">
                Create YouTube channel
              </a>
            </>
          ) : null}
        </div>
      ) : null}

      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
        {props.onConnectOrReconnect ? (
          <Button appearance={hasSavedCredential ? 'outline' : 'primary'} size="small" onClick={props.onConnectOrReconnect} disabled={props.connectionLoading}>
            {props.connectionLoading ? 'Starting…' : connectLabel}
          </Button>
        ) : null}
        {props.onTestConnection && hasSavedCredential ? (
          <Button appearance="outline" size="small" onClick={props.onTestConnection} disabled={props.validationLoading}>
            {props.validationLoading ? 'Testing…' : 'Test connection'}
          </Button>
        ) : null}
        {shouldShowPersist && props.onPersistConnection ? (
          <Button appearance="primary" size="small" onClick={props.onPersistConnection} disabled={props.persistLoading}>
            {props.persistLoading ? 'Saving…' : 'Persist connection for future use by Agent'}
          </Button>
        ) : null}
        {isAttached ? <Badge appearance="outline" color="success">Attached to this hire</Badge> : null}
      </div>
    </Container>
  )
}

export default DigitalMarketingChannelStatusCard