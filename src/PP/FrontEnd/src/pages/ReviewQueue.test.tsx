import '@testing-library/jest-dom/vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { expect, test, vi } from 'vitest'

import ReviewQueue from './ReviewQueue'

const mocks = vi.hoisted(() => {
  return {
    listMarketingDraftBatches: vi.fn(async () => [
      {
        batch_id: 'BATCH-1',
        agent_id: 'AGT-MKT-HEALTH-001',
        customer_id: 'CUST-001',
        theme: 'Healthy habits',
        brand_name: 'Care Clinic',
        status: 'pending_review',
        posts: [
          { post_id: 'POST-1', channel: 'linkedin', text: 'Hello', review_status: 'pending_review' }
        ]
      }
    ]),
    approveMarketingDraftPost: vi.fn(async () => ({ post_id: 'POST-1', review_status: 'approved', approval_id: 'APR-123' })),
    scheduleMarketingDraftPost: vi.fn(async () => ({ post_id: 'POST-1', execution_status: 'scheduled', scheduled_at: '2026-02-06T00:00:00+00:00' }))
  }
})

vi.mock('../services/gatewayApiClient', () => {
  return vi.importActual<any>('../services/gatewayApiClient').then((actual) => {
    return {
      ...actual,
      gatewayApiClient: {
        ...(actual.gatewayApiClient || {}),
        listMarketingDraftBatches: mocks.listMarketingDraftBatches,
        approveMarketingDraftPost: mocks.approveMarketingDraftPost,
        scheduleMarketingDraftPost: mocks.scheduleMarketingDraftPost
      }
    }
  })
})

test('ReviewQueue loads batches and approves a post', async () => {
  render(<ReviewQueue />)

  fireEvent.click(screen.getByRole('button', { name: 'Load' }))

  await waitFor(() => {
    expect(mocks.listMarketingDraftBatches).toHaveBeenCalledTimes(1)
  })

  fireEvent.click(screen.getByRole('button', { name: 'Approve' }))

  await waitFor(() => {
    expect(mocks.approveMarketingDraftPost).toHaveBeenCalledTimes(1)
  })

  fireEvent.change(
    screen.getByRole('textbox', { name: /scheduled_at/i }),
    { target: { value: '2026-02-06T00:00:00+00:00' } }
  )
  fireEvent.click(screen.getByRole('button', { name: 'Schedule' }))

  await waitFor(() => {
    expect(mocks.scheduleMarketingDraftPost).toHaveBeenCalledTimes(1)
  })
})
