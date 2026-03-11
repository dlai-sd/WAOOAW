import '@testing-library/jest-dom/vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
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
    expect(screen.getByRole('heading', { name: 'Usage Events' })).toBeInTheDocument()
  })

  expect(mocks.listUsageEvents).not.toHaveBeenCalled()
  expect(mocks.aggregateUsageEvents).not.toHaveBeenCalled()

  await screen.findByText('Start with a customer or agent filter')
  await screen.findByText('Load aggregates after choosing the scope')
  expect(screen.queryByText('No usage events returned.')).not.toBeInTheDocument()
  expect(screen.queryByText('No aggregate rows returned.')).not.toBeInTheDocument()

  const customerInput = screen.getByPlaceholderText('CUST-1')
  const loadUsageButton = screen.getByRole('button', { name: 'Load usage' })
  const loadAggregatesButton = screen.getByRole('button', { name: 'Load aggregates' })

  fireEvent.change(customerInput, { target: { value: 'CUST-1' } })

  await waitFor(() => {
    expect((customerInput as HTMLInputElement).value).toBe('CUST-1')
  })

  fireEvent.click(loadUsageButton)
  fireEvent.click(loadAggregatesButton)

  await waitFor(() => {
    expect(mocks.listUsageEvents).toHaveBeenCalled()
  })

  await waitFor(() => {
    expect(mocks.aggregateUsageEvents).toHaveBeenCalled()
  })

  expect(mocks.listUsageEvents).toHaveBeenLastCalledWith({
    customer_id: 'CUST-1',
    agent_id: undefined,
    limit: 100
  })

  expect(mocks.aggregateUsageEvents).toHaveBeenLastCalledWith({
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
