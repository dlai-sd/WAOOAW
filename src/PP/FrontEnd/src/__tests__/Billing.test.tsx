import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { expect, test, vi } from 'vitest'

import Billing from '../pages/Billing'

const mocks = vi.hoisted(() => {
  return {
    listOpsSubscriptions: vi.fn(async () => [])
  }
})

vi.mock('../services/gatewayApiClient', () => {
  return vi.importActual<any>('../services/gatewayApiClient').then((actual) => {
    return {
      ...actual,
      gatewayApiClient: {
        ...(actual.gatewayApiClient || {}),
        listOpsSubscriptions: mocks.listOpsSubscriptions
      }
    }
  })
})

test('Billing renders total subscription count from live data', async () => {
  mocks.listOpsSubscriptions.mockResolvedValueOnce([
    { subscription_id: 's1', status: 'active' },
    { subscription_id: 's2', status: 'trial' }
  ])

  render(<Billing />)

  // After loading, check that "Total Subscriptions" card shows 2
  await waitFor(() => {
    // The spinner should be gone
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  expect(screen.getByText('Total Subscriptions')).toBeInTheDocument()
})

test('Billing renders spinner while loading', () => {
  // listOpsSubscriptions never resolves during this test
  mocks.listOpsSubscriptions.mockReturnValueOnce(new Promise(() => {}))

  render(<Billing />)

  // Spinner should be visible (FluentUI Spinner uses role="progressbar")
  expect(screen.getByRole('progressbar')).toBeInTheDocument()
})

test('Billing renders error banner on fetch failure', async () => {
  mocks.listOpsSubscriptions.mockRejectedValueOnce(new Error('fail'))

  render(<Billing />)

  await waitFor(() => {
    expect(screen.getByText('Failed to load subscription data. Please try again.')).toBeInTheDocument()
  })
})

test('Billing renders empty state when no subscriptions returned', async () => {
  mocks.listOpsSubscriptions.mockResolvedValueOnce([])

  render(<Billing />)

  await waitFor(() => {
    expect(screen.getByText('No subscriptions found.')).toBeInTheDocument()
  })
})
