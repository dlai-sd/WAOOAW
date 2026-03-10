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
  render(
    <MemoryRouter initialEntries={['/review-queue']}>
      <Routes>
        <Route path="/review-queue" element={<ReviewQueue />} />
      </Routes>
    </MemoryRouter>
  )

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

test('ReviewQueue preserves operator context for the next PP surface', async () => {
  const user = userEvent.setup()

  render(
    <MemoryRouter initialEntries={['/review-queue?customer_id=CUST-001&agent_id=AGT-MKT-HEALTH-001']}>
      <Routes>
        <Route path="/review-queue" element={<ReviewQueue />} />
        <Route path="/hired-agents" element={<LocationEcho />} />
      </Routes>
    </MemoryRouter>
  )

  await waitFor(() => {
    expect(mocks.listMarketingDraftBatches).toHaveBeenCalledWith({
      customer_id: 'CUST-001',
      agent_id: 'AGT-MKT-HEALTH-001',
      limit: 20
    })
  })

  expect(screen.getByText('Operator handoff context')).toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: 'Open Hired Agents' }))

  await waitFor(() => {
    expect(screen.getByTestId('location-display')).toHaveTextContent('/hired-agents?customer_id=CUST-001&agent_id=AGT-MKT-HEALTH-001')
  })
})
