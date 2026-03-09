import '@testing-library/jest-dom/vitest'
import { render, screen } from '@testing-library/react'
import { expect, test, vi } from 'vitest'

import ReviewQueue from '../pages/ReviewQueue'

vi.mock('../services/gatewayApiClient', () => ({
  gatewayApiClient: {
    listMarketingDraftBatches: vi.fn(async () => []),
    approveMarketingDraftPost: vi.fn(async () => ({})),
    scheduleMarketingDraftPost: vi.fn(async () => ({})),
  },
}))

vi.mock('../components/ApiErrorPanel', () => ({
  default: ({ title }: { title: string }) => <div>{title}</div>,
}))

test('ReviewQueue renders with empty Customer ID input on load', () => {
  render(<ReviewQueue />)

  const customerIdInput = screen.getByRole('textbox', { name: /customer id/i })
  expect(customerIdInput).toHaveValue('')
})

test('ReviewQueue renders with empty Agent ID input on load', () => {
  render(<ReviewQueue />)

  const agentIdInput = screen.getByRole('textbox', { name: /agent id/i })
  expect(agentIdInput).toHaveValue('')
})
