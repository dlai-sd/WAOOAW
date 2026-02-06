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
    })),
    aggregateUsageEvents: vi.fn(async () => ({
      count: 1,
      rows: [
        {
          bucket: 'day',
          bucket_start: '2026-02-06T00:00:00Z',
          event_type: 'skill_execution',
          event_count: 1,
          tokens_in: 11,
          tokens_out: 22,
          cost_usd: 0.1
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
        listUsageEvents: mocks.listUsageEvents,
        aggregateUsageEvents: mocks.aggregateUsageEvents
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

  await waitFor(() => {
    expect(mocks.aggregateUsageEvents).toHaveBeenCalledTimes(1)
  })

  expect(mocks.listUsageEvents).toHaveBeenCalledWith({
    customer_id: 'CUST-1',
    agent_id: undefined,
    limit: 100
  })

  expect(mocks.aggregateUsageEvents).toHaveBeenCalledWith({
    bucket: 'day',
    customer_id: 'CUST-1',
    agent_id: undefined
  })

  await waitFor(() => {
    expect(screen.getAllByText('skill_execution').length).toBeGreaterThanOrEqual(1)
  })

  expect(screen.getByText('AGT-MKT-CAKE-001')).toBeInTheDocument()
  expect(screen.getByText('gpt-4o-mini')).toBeInTheDocument()
  expect(screen.getAllByText('11/22').length).toBeGreaterThanOrEqual(1)
  expect(screen.getByText('corr-123')).toBeInTheDocument()

  await waitFor(() => {
    expect(screen.getByText('Usage Aggregates')).toBeInTheDocument()
  })
  expect(screen.getByText('2026-02-06')).toBeInTheDocument()
})
