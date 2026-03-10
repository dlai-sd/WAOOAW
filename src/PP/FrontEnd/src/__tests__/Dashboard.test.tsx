import '@testing-library/jest-dom/vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { expect, test, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  listAgents: vi.fn()
}))

vi.mock('../services/gatewayApiClient', () => ({
  gatewayApiClient: {
    listAgents: mocks.listAgents,
  }
}))

import { Dashboard } from '../pages/Dashboard'

test('E10-S1-T1: dashboard does not auto-load live counts before the operator asks for them', () => {
  render(<Dashboard />)

  expect(mocks.listAgents).not.toHaveBeenCalled()
  expect(screen.getByText('Not loaded')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Load live count' })).toBeInTheDocument()
})

test('E10-S1-T2: Active Agents card shows count when the operator explicitly loads it', async () => {
  mocks.listAgents.mockResolvedValueOnce([{}, {}, {}, {}, {}])

  render(<Dashboard />)

  fireEvent.click(screen.getByRole('button', { name: 'Load live count' }))

  await waitFor(() => {
    expect(screen.getByText('5')).toBeInTheDocument()
  })
})

test('E10-S1-T3: Active Agents card shows an unavailable state when the live load fails', async () => {
  mocks.listAgents.mockRejectedValueOnce(new Error('Network error'))

  render(<Dashboard />)

  fireEvent.click(screen.getByRole('button', { name: 'Load live count' }))

  await waitFor(() => {
    expect(screen.getByText('Unavailable')).toBeInTheDocument()
  })
  expect(screen.queryByText('5')).not.toBeInTheDocument()
})

test('E10-S1-T4: dashboard cards stay honest about live posture instead of showing fake metrics', () => {
  render(<Dashboard />)

  expect(screen.getByText('Check live queues')).toBeInTheDocument()
  expect(screen.getByText('Needs verification')).toBeInTheDocument()
  expect(screen.getByText('Choose a surface')).toBeInTheDocument()
})
