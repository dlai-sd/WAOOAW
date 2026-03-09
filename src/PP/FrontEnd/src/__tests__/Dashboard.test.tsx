import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { expect, test, vi } from 'vitest'

const mockListAgents = vi.fn()

vi.mock('../services/gatewayApiClient', () => ({
  gatewayApiClient: {
    listAgents: mockListAgents,
  },
}))

import { Dashboard } from '../pages/Dashboard'

test('E10-S1-T1: Active Agents card shows count when listAgents returns 5 items', async () => {
  mockListAgents.mockResolvedValueOnce([{}, {}, {}, {}, {}])

  render(<Dashboard />)

  await waitFor(() => {
    expect(screen.getByText('5')).toBeInTheDocument()
  })
})

test('E10-S1-T2: Active Agents card shows "—" when listAgents throws', async () => {
  mockListAgents.mockRejectedValueOnce(new Error('Network error'))

  render(<Dashboard />)

  await waitFor(() => {
    expect(screen.getByText('—')).toBeInTheDocument()
  })
  expect(screen.queryByText('5')).not.toBeInTheDocument()
})

test('E10-S1-T3: MRR, Customers, and Churn Rate cards show "Coming soon" (3 times)', async () => {
  mockListAgents.mockResolvedValueOnce([])

  render(<Dashboard />)

  await waitFor(() => {
    const comingSoonItems = screen.getAllByText('Coming soon')
    expect(comingSoonItems).toHaveLength(3)
  })
})
