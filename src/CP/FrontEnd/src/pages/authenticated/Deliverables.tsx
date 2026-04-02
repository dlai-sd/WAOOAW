import { Badge, Button, Card, Input, Spinner } from '@fluentui/react-components'
import { useEffect, useMemo, useState } from 'react'

import {
  listHiredAgentDeliverables,
  reviewHiredAgentDeliverable,
  type Deliverable,
} from '../../services/hiredAgentDeliverables.service'
import { getMyAgentsSummary } from '../../services/myAgentsSummary.service'

const REVIEW_BADGE_COLOR: Record<string, 'warning' | 'success' | 'danger' | 'informative'> = {
  pending_review: 'warning',
  approved: 'success',
  rejected: 'danger',
}

function formatDeliverableDate(value?: string | null): string {
  if (!value) return 'Date unavailable'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleString()
}

function getPayloadPreview(payload: Record<string, unknown>): string {
  const previewKeys = ['summary', 'text_preview', 'preview', 'content'] as const

  for (const key of previewKeys) {
    const value = payload[key]
    const normalized = typeof value === 'string' ? value.trim() : ''
    if (normalized) {
      return normalized.length > 120 ? `${normalized.slice(0, 120)}…` : normalized
    }
  }

  return 'Preview unavailable for this deliverable.'
}

export default function Deliverables() {
  const [deliverables, setDeliverables] = useState<Deliverable[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reviewLoading, setReviewLoading] = useState<Record<string, boolean>>({})
  const [reviewErrors, setReviewErrors] = useState<Record<string, string>>({})
  const [rejectingId, setRejectingId] = useState<string | null>(null)
  const [rejectNotes, setRejectNotes] = useState<Record<string, string>>({})

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const summary = await getMyAgentsSummary()
        const instances = (summary?.instances || []).filter((instance) =>
          String(instance.hired_instance_id || '').trim()
        )

        if (!instances.length) {
          if (!cancelled) {
            setDeliverables([])
          }
          return
        }

        const results = await Promise.allSettled(
          instances.map((instance) =>
            listHiredAgentDeliverables(String(instance.hired_instance_id))
          )
        )

        const nextDeliverables: Deliverable[] = []
        const hadFailure = results.some((result) => result.status === 'rejected')

        for (const result of results) {
          if (result.status === 'fulfilled' && result.value?.deliverables) {
            nextDeliverables.push(...result.value.deliverables)
          }
        }

        nextDeliverables.sort((a, b) =>
          String(b.created_at || '').localeCompare(String(a.created_at || ''))
        )

        if (!cancelled) {
          if (hadFailure && nextDeliverables.length === 0) {
            setError('Failed to load deliverables. Please try again.')
          } else {
            setDeliverables(nextDeliverables)
          }
        }
      } catch {
        if (!cancelled) {
          setError('Failed to load deliverables. Please try again.')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void load()

    return () => {
      cancelled = true
    }
  }, [])

  const sortedDeliverables = useMemo(
    () =>
      [...deliverables].sort((a, b) =>
        String(b.created_at || '').localeCompare(String(a.created_at || ''))
      ),
    [deliverables]
  )

  async function handleReview(
    deliverableId: string,
    decision: 'approved' | 'rejected',
    notes?: string
  ) {
    setReviewLoading((current) => ({ ...current, [deliverableId]: true }))
    setReviewErrors((current) => {
      const next = { ...current }
      delete next[deliverableId]
      return next
    })

    try {
      await reviewHiredAgentDeliverable(deliverableId, {
        decision,
        notes: notes?.trim() || undefined,
      })

      setDeliverables((current) =>
        current.map((deliverable) =>
          deliverable.deliverable_id === deliverableId
            ? {
                ...deliverable,
                review_status: decision,
                review_notes: notes?.trim() || deliverable.review_notes || null,
              }
            : deliverable
        )
      )
      setRejectingId(null)
      setRejectNotes((current) => ({ ...current, [deliverableId]: '' }))
    } catch {
      setReviewErrors((current) => ({
        ...current,
        [deliverableId]: 'Failed to update review. Please try again.',
      }))
    } finally {
      setReviewLoading((current) => ({ ...current, [deliverableId]: false }))
    }
  }

  if (loading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <Spinner label="Loading deliverables..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="deliverables-page">
        <div className="page-header" style={{ marginBottom: '24px' }}>
          <h1>Deliverables</h1>
        </div>
        <div className="error-banner" style={{ padding: '1rem', color: '#ef4444' }}>
          {error}
        </div>
      </div>
    )
  }

  if (!sortedDeliverables.length) {
    return (
      <div className="deliverables-page">
        <div className="page-header" style={{ marginBottom: '24px' }}>
          <h1>Deliverables</h1>
          <p style={{ color: 'var(--colorNeutralForeground2)', marginTop: '4px' }}>
            Everything your agents have produced — filter by agent, date, or goal.
          </p>
        </div>
        <Card style={{ padding: '2rem', textAlign: 'center', opacity: 0.7 }}>
          No deliverables yet. Once your agents start working, their output will appear here.
        </Card>
      </div>
    )
  }

  return (
    <div className="deliverables-page">
      <div className="page-header" style={{ marginBottom: '24px' }}>
        <h1>Deliverables</h1>
        <p style={{ color: 'var(--colorNeutralForeground2)', marginTop: '4px' }}>
          Everything your agents have produced — filter by agent, date, or goal.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {sortedDeliverables.map((deliverable) => {
          const reviewStatus = String(deliverable.review_status || 'pending_review').trim().toLowerCase()
          const preview = getPayloadPreview(deliverable.payload || {})
          const isPendingReview = reviewStatus === 'pending_review'
          const isRejecting = rejectingId === deliverable.deliverable_id
          const isReviewing = Boolean(reviewLoading[deliverable.deliverable_id])

          return (
            <Card key={deliverable.deliverable_id} style={{ padding: '16px' }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  flexWrap: 'wrap',
                  gap: '12px',
                }}
              >
                <div style={{ flex: 1, minWidth: '240px' }}>
                  <div style={{ fontWeight: 700, marginBottom: '4px' }}>{deliverable.title}</div>
                  <div style={{ fontSize: '13px', color: 'var(--colorNeutralForeground2)' }}>
                    {formatDeliverableDate(deliverable.created_at)}
                  </div>
                  <div
                    style={{
                      fontSize: '13px',
                      color: 'var(--colorNeutralForeground3)',
                      marginTop: '8px',
                      lineHeight: 1.5,
                    }}
                  >
                    {preview}
                  </div>

                  {reviewErrors[deliverable.deliverable_id] ? (
                    <div style={{ color: '#ef4444', fontSize: '12px', marginTop: '8px' }}>
                      {reviewErrors[deliverable.deliverable_id]}
                    </div>
                  ) : null}

                  {isPendingReview ? (
                    <div style={{ marginTop: '12px', display: 'grid', gap: '8px' }}>
                      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                        <Button
                          appearance="primary"
                          disabled={isReviewing}
                          onClick={() => void handleReview(deliverable.deliverable_id, 'approved')}
                        >
                          {isReviewing ? 'Approving…' : 'Approve'}
                        </Button>
                        <Button
                          appearance="secondary"
                          disabled={isReviewing}
                          onClick={() =>
                            setRejectingId((current) =>
                              current === deliverable.deliverable_id ? null : deliverable.deliverable_id
                            )
                          }
                        >
                          Reject
                        </Button>
                        {isReviewing ? <Spinner size="tiny" /> : null}
                      </div>

                      {isRejecting ? (
                        <div style={{ display: 'grid', gap: '8px', maxWidth: '420px' }}>
                          <Input
                            aria-label={`Rejection notes for ${deliverable.title}`}
                            placeholder="Add rejection notes"
                            value={rejectNotes[deliverable.deliverable_id] || ''}
                            onChange={(_, data) =>
                              setRejectNotes((current) => ({
                                ...current,
                                [deliverable.deliverable_id]: data.value,
                              }))
                            }
                          />
                          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                            <Button
                              appearance="primary"
                              disabled={isReviewing}
                              onClick={() =>
                                void handleReview(
                                  deliverable.deliverable_id,
                                  'rejected',
                                  rejectNotes[deliverable.deliverable_id]
                                )
                              }
                            >
                              Confirm rejection
                            </Button>
                            <Button
                              appearance="subtle"
                              disabled={isReviewing}
                              onClick={() => setRejectingId(null)}
                            >
                              Cancel
                            </Button>
                          </div>
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                </div>

                <Badge
                  appearance="filled"
                  color={REVIEW_BADGE_COLOR[reviewStatus] || 'informative'}
                >
                  {reviewStatus}
                </Badge>
              </div>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
