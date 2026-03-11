import '@testing-library/jest-dom/vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { expect, test, vi } from 'vitest'

import ReviewQueue from './ReviewQueue'

function LocationEcho() {
  const location = useLocation()
  return <div data-testid="location-display">{`${location.pathname}${location.search}`}</div>
}

const mocks = vi.hoisted(() => {
  return {
    listReviewQueueApprovals: vi.fn(async () => ({
      count: 1,
      approvals: [
        {
          approval_id: 'APR-123',
          customer_id: 'CUST-001',
          customer_label: 'CUST-001',
          agent_id: 'AGT-MKT-HEALTH-001',
          agent_label: 'Healthcare Content Agent',
          action: 'publish',
          requested_by: 'admin-1',
          correlation_id: 'corr-1',
          purpose: 'review_queue',
          notes: 'Check tone before publish',
          created_at: '2026-03-10T12:00:00Z',
          expires_at: null,
          hired_instance_id: 'HIRE-1',
          review_state: 'pending_review',
          deliverable_preview: {
            batch_id: 'BATCH-1',
            post_id: 'POST-1',
            brand_name: 'Care Clinic',
            theme: 'Healthy habits',
            channel: 'linkedin',
            text_preview: 'Hello',
          },
        }
      ]
    })),
    approveMarketingDraftPost: vi.fn(async () => ({ post_id: 'POST-1', review_status: 'approved', approval_id: 'APR-123' })),
    rejectMarketingDraftPost: vi.fn(async () => ({ post_id: 'POST-1', review_status: 'rejected' })),
    listOpsHiredAgentDeliverables: vi.fn(async () => ({
      deliverables: [
        {
          deliverable_id: 'DEL-1',
          approval_id: 'APR-123',
          review_status: 'approved',
          execution_status: 'scheduled',
          created_at: '2026-03-10T12:00:00Z',
          payload: {
            destination: { destination_type: 'youtube', metadata: { visibility: 'private' } },
            publish_status: 'not_published'
          }
        }
      ]
    })),
    listOpsPlatformConnections: vi.fn(async () => ([])),
  }
})

vi.mock('../services/gatewayApiClient', () => {
  return vi.importActual<any>('../services/gatewayApiClient').then((actual) => {
    return {
      ...actual,
      gatewayApiClient: {
        ...(actual.gatewayApiClient || {}),
        listReviewQueueApprovals: mocks.listReviewQueueApprovals,
        approveMarketingDraftPost: mocks.approveMarketingDraftPost,
        rejectMarketingDraftPost: mocks.rejectMarketingDraftPost,
        listOpsHiredAgentDeliverables: mocks.listOpsHiredAgentDeliverables,
        listOpsPlatformConnections: mocks.listOpsPlatformConnections,
      }
    }
  })
})

test('ReviewQueue loads enriched approvals and can approve or deny a selected item', async () => {
  render(
    <MemoryRouter
      initialEntries={['/review-queue']}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path="/review-queue" element={<ReviewQueue />} />
      </Routes>
    </MemoryRouter>
  )

  fireEvent.click(screen.getByRole('button', { name: 'Load' }))

  await waitFor(() => {
    expect(mocks.listReviewQueueApprovals).toHaveBeenCalledTimes(1)
  })

  expect(screen.getByText('Decision workspace')).toBeInTheDocument()
  expect(screen.getByText('Healthcare Content Agent')).toBeInTheDocument()
  await waitFor(() => {
    expect(screen.getByTestId('pp-review-queue-publish-readiness')).toHaveTextContent('Blocked by channel connection')
  })
  expect(screen.getByTestId('pp-review-queue-channel-status')).toHaveTextContent('Youtube not connected')

  fireEvent.click(screen.getByRole('button', { name: 'Approve and remove' }))

  await waitFor(() => {
    expect(mocks.approveMarketingDraftPost).toHaveBeenCalledTimes(1)
  })

  expect(screen.queryByText('Healthcare Content Agent')).not.toBeInTheDocument()

  mocks.listReviewQueueApprovals.mockResolvedValueOnce({
    count: 1,
    approvals: [
      {
        approval_id: 'APR-456',
        customer_id: 'CUST-001',
        customer_label: 'CUST-001',
        agent_id: 'AGT-MKT-HEALTH-001',
        agent_label: 'Healthcare Content Agent',
        action: 'publish',
        requested_by: 'admin-1',
        correlation_id: 'corr-1',
        purpose: 'review_queue',
        notes: 'Check tone before publish',
        created_at: '2026-03-10T12:00:00Z',
        expires_at: null,
        hired_instance_id: 'HIRE-1',
        review_state: 'pending_review',
        deliverable_preview: {
          batch_id: 'BATCH-1',
          post_id: 'POST-1',
          brand_name: 'Care Clinic',
          theme: 'Healthy habits',
          channel: 'linkedin',
          text_preview: 'Hello',
        },
      }
    ]
  })

  fireEvent.click(screen.getByRole('button', { name: 'Load' }))

  await waitFor(() => {
    expect(screen.getByText('Healthcare Content Agent')).toBeInTheDocument()
  })

  fireEvent.click(screen.getByRole('button', { name: 'Deny and remove' }))

  await waitFor(() => {
    expect(mocks.rejectMarketingDraftPost).toHaveBeenCalledTimes(1)
  })
})

test('ReviewQueue preserves operator context for the next PP surface', async () => {
  const user = userEvent.setup()

  render(
    <MemoryRouter
      initialEntries={['/review-queue?customer_id=CUST-001&agent_id=AGT-MKT-HEALTH-001&correlation_id=corr-1']}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path="/review-queue" element={<ReviewQueue />} />
        <Route path="/hired-agents" element={<LocationEcho />} />
      </Routes>
    </MemoryRouter>
  )

  await waitFor(() => {
    expect(mocks.listReviewQueueApprovals).toHaveBeenCalledWith({
      customer_id: 'CUST-001',
      agent_id: 'AGT-MKT-HEALTH-001',
      correlation_id: 'corr-1',
      limit: 20
    })
  })

  expect(screen.getByText('Operator handoff context')).toBeInTheDocument()

  await waitFor(() => {
    expect(screen.getByTestId('pp-review-queue-block-owner')).toHaveTextContent('Platform action required')
  })

  await user.click(screen.getByRole('button', { name: 'Open runtime context' }))

  await waitFor(() => {
    expect(screen.getByTestId('location-display')).toHaveTextContent('/hired-agents?customer_id=CUST-001&agent_id=AGT-MKT-HEALTH-001&correlation_id=corr-1&selected_hired_instance_id=HIRE-1')
  })
})
