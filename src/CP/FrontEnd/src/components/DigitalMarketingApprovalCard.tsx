import { Button, Card, Textarea } from '@fluentui/react-components'

import { SaveIndicator } from './FeedbackIndicators'
import { type Deliverable } from '../services/hiredAgentDeliverables.service'

type DigitalMarketingApprovalCardProps = {
  deliverable: Deliverable
  reviewNotes: string
  reviewing: boolean
  reviewSaved: boolean
  readOnly: boolean
  embedded?: boolean
  onReviewNotesChange: (value: string) => void
  onApprove: () => void
  onReject: () => void
}

export function DigitalMarketingApprovalCard(props: DigitalMarketingApprovalCardProps) {
  const reviewStatus = String(props.deliverable.review_status || '').trim().toLowerCase() || 'pending_review'
  const statusLabel = reviewStatus.replace(/_/g, ' ')
  const Container = props.embedded ? 'div' : Card
  const containerProps = props.embedded
    ? { style: { display: 'flex', flexDirection: 'column' as const, gap: '12px' } }
    : { style: { padding: '16px', display: 'flex', flexDirection: 'column' as const, gap: '12px' } }

  return (
    <Container {...containerProps}>
      <div>
        <div style={{ fontWeight: 700, marginBottom: '4px' }}>Customer approval</div>
        <div style={{ fontSize: '13px', color: 'var(--colorNeutralForeground2)' }}>
          This exact deliverable must be approved before the agent can take any external YouTube action.
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
        <div>
          <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground3)', marginBottom: '4px' }}>Review state</div>
          <div style={{ fontWeight: 600, textTransform: 'capitalize' }}>{statusLabel}</div>
        </div>
        <div>
          <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground3)', marginBottom: '4px' }}>Approval reference</div>
          <div style={{ fontWeight: 600 }}>{props.deliverable.approval_id || 'Not issued yet'}</div>
        </div>
      </div>

      <div>
        <div style={{ fontWeight: 600, marginBottom: '6px' }}>Review notes</div>
        <Textarea
          aria-label="Review notes"
          value={props.reviewNotes}
          disabled={props.readOnly || props.reviewing}
          onChange={(_, data) => props.onReviewNotesChange(String(data.value || ''))}
          placeholder="Explain what should change or confirm what you approve"
        />
      </div>

      <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
        <Button appearance="primary" disabled={props.readOnly || props.reviewing} onClick={props.onApprove}>
          Approve exact deliverable
        </Button>
        <Button appearance="outline" disabled={props.readOnly || props.reviewing} onClick={props.onReject}>
          Reject and request revision
        </Button>
        <SaveIndicator status={props.reviewing ? 'saving' : props.reviewSaved ? 'saved' : 'idle'} />
      </div>
    </Container>
  )
}

export default DigitalMarketingApprovalCard