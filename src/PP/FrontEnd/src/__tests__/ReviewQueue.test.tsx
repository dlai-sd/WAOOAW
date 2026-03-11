import '@testing-library/jest-dom/vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { expect, test, vi } from 'vitest'

import ReviewQueue from '../pages/ReviewQueue'

vi.mock('../services/gatewayApiClient', () => ({
  gatewayApiClient: {
    listReviewQueueApprovals: vi.fn(async () => ({ approvals: [] })),
    approveMarketingDraftPost: vi.fn(async () => ({})),
    rejectMarketingDraftPost: vi.fn(async () => ({})),
    listOpsHiredAgentDeliverables: vi.fn(async () => ({ deliverables: [] })),
    listOpsPlatformConnections: vi.fn(async () => ([])),
  },
}))

vi.mock('../components/ApiErrorPanel', () => ({
  default: ({ title }: { title: string }) => <div>{title}</div>,
}))

test('ReviewQueue renders with empty Customer ID input on load', () => {
  render(
    <MemoryRouter initialEntries={['/review-queue']}>
      <Routes>
        <Route path="/review-queue" element={<ReviewQueue />} />
      </Routes>
    </MemoryRouter>
  )

  const customerIdInput = screen.getByRole('textbox', { name: /customer id/i })
  expect(customerIdInput).toHaveValue('')
})

test('ReviewQueue renders with empty Agent ID input on load', () => {
  render(
    <MemoryRouter initialEntries={['/review-queue']}>
      <Routes>
        <Route path="/review-queue" element={<ReviewQueue />} />
      </Routes>
    </MemoryRouter>
  )

  const agentIdInput = screen.getByRole('textbox', { name: /agent id/i })
  expect(agentIdInput).toHaveValue('')
})
