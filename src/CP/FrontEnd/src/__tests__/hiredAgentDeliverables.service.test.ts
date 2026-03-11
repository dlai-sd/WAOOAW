import { describe, expect, it } from 'vitest'

import {
  getDeliverablePublishReadiness,
  type Deliverable,
} from '../services/hiredAgentDeliverables.service'

function buildDeliverable(overrides: Partial<Deliverable> = {}): Deliverable {
  return {
    deliverable_id: 'DEL-1',
    hired_instance_id: 'HIRED-1',
    goal_instance_id: 'GOAL-1',
    goal_template_id: 'TPL-1',
    title: 'YouTube draft',
    payload: {
      destination: {
        destination_type: 'youtube',
        metadata: {
          visibility: 'private',
        },
      },
    },
    review_status: 'pending_review',
    execution_status: 'not_executed',
    ...overrides,
  }
}

describe('hiredAgentDeliverables.service', () => {
  it('returns blocked-by-approval before a deliverable is approved', () => {
    const readiness = getDeliverablePublishReadiness(buildDeliverable(), {
      hasPlatformConnection: true,
      platformLabel: 'YouTube',
    })

    expect(readiness.key).toBe('blocked_missing_approval')
    expect(readiness.label).toBe('Blocked by approval')
  })

  it('returns blocked-by-missing-channel-connection for approved deliverables without YouTube access', () => {
    const readiness = getDeliverablePublishReadiness(
      buildDeliverable({ review_status: 'approved', approval_id: 'APR-1' }),
      {
        hasPlatformConnection: false,
        platformLabel: 'YouTube',
      }
    )

    expect(readiness.key).toBe('blocked_missing_channel_connection')
    expect(readiness.label).toBe('Blocked by missing channel connection')
  })

  it('returns ready-for-upload when approval and YouTube readiness are both satisfied', () => {
    const readiness = getDeliverablePublishReadiness(
      buildDeliverable({ review_status: 'approved', approval_id: 'APR-1' }),
      {
        hasPlatformConnection: true,
        platformLabel: 'YouTube',
      }
    )

    expect(readiness.key).toBe('ready_for_upload')
    expect(readiness.label).toBe('Ready for upload')
  })

  it('returns uploaded-non-public after execution completes without public release', () => {
    const readiness = getDeliverablePublishReadiness(
      buildDeliverable({
        review_status: 'approved',
        approval_id: 'APR-1',
        execution_status: 'executed',
      }),
      {
        hasPlatformConnection: true,
        platformLabel: 'YouTube',
      }
    )

    expect(readiness.key).toBe('uploaded_non_public')
    expect(readiness.label).toBe('Uploaded as non-public')
  })
})