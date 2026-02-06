import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { expect, test, vi } from 'vitest'

import CustomerManagement from './CustomerManagement'

const mocks = vi.hoisted(() => {
  return {
    listUsageEvents: vi.fn(async () => ({
      count: 1,
      events: [
        {
          event_type: 'skill_execution',
          timestamp: '2026-02-06T00:00:00Z',
          agent_id: 'AGT-MKT-CAKE-001',
          model: 'gpt-4o-mini',
          tokens_in: 11,
          tokens_out: 22,
          cost_usd: 0.1,
          correlation_id: 'corr-123'
        }
      ]
    }))
  }
})

vi.mock('../services/gatewayApiClient', () => {
  return vi.importActual<any>('../services/gatewayApiClient').then((actual) => {
    return {
      ...actual,
      gatewayApiClient: {
        ...(actual.gatewayApiClient || {}),
        listUsageEvents: mocks.listUsageEvents
      }
    }
  })
})

test('CustomerManagement renders usage events from API', async () => {
  render(<CustomerManagement />)

  await waitFor(() => {
    expect(screen.getByText('Usage Events')).toBeInTheDocument()
  })

  await waitFor(() => {
    expect(mocks.listUsageEvents).toHaveBeenCalledTimes(1)
  })

  expect(mocks.listUsageEvents).toHaveBeenCalledWith({
    customer_id: 'CUST-1',
    agent_id: undefined,
    limit: 100
  })

  await waitFor(() => {
    expect(screen.getByText('skill_execution')).toBeInTheDocument()
  })

  expect(screen.getByText('AGT-MKT-CAKE-001')).toBeInTheDocument()
  expect(screen.getByText('gpt-4o-mini')).toBeInTheDocument()
  expect(screen.getByText('11/22')).toBeInTheDocument()
  expect(screen.getByText('corr-123')).toBeInTheDocument()
})
