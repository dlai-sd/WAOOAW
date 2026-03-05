/**
 * Unit tests for the new ops-specific methods added to gatewayApiClient.
 * Tests verify that URLs are built correctly by the listOps* methods.
 */
import '@testing-library/jest-dom/vitest'
import { expect, test, vi, beforeEach } from 'vitest'

// Mock the entire gatewayApiClient to avoid browser environment issues
// but test only the URL-building logic via withQuery.
// We verify the methods exist and call fetch with the correct URL pattern.

// Mock fetch globally
const fetchMock = vi.fn(async () =>
  new Response(JSON.stringify([]), {
    status: 200,
    headers: { 'Content-Type': 'application/json' }
  })
)
global.fetch = fetchMock

beforeEach(() => {
  fetchMock.mockClear()
  localStorage.clear()
})

test('gatewayApiClient has listOpsSubscriptions method', async () => {
  const { gatewayApiClient } = await import('../services/gatewayApiClient')
  expect(typeof gatewayApiClient.listOpsSubscriptions).toBe('function')
})

test('gatewayApiClient has listOpsHiredAgents method', async () => {
  const { gatewayApiClient } = await import('../services/gatewayApiClient')
  expect(typeof gatewayApiClient.listOpsHiredAgents).toBe('function')
})

test('gatewayApiClient has listOpsHiredAgentGoals method', async () => {
  const { gatewayApiClient } = await import('../services/gatewayApiClient')
  expect(typeof gatewayApiClient.listOpsHiredAgentGoals).toBe('function')
})

test('gatewayApiClient has listOpsHiredAgentDeliverables method', async () => {
  const { gatewayApiClient } = await import('../services/gatewayApiClient')
  expect(typeof gatewayApiClient.listOpsHiredAgentDeliverables).toBe('function')
})

test('listOpsSubscriptions builds URL with /pp/ops/subscriptions and customer_id param', async () => {
  const { gatewayApiClient } = await import('../services/gatewayApiClient')
  fetchMock.mockResolvedValueOnce(
    new Response(JSON.stringify([]), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    })
  )
  await gatewayApiClient.listOpsSubscriptions({ customer_id: 'C1' })
  expect(fetchMock).toHaveBeenCalledTimes(1)
  const calledUrl: string = fetchMock.mock.calls[0][0] as string
  expect(calledUrl).toContain('/pp/ops/subscriptions')
  expect(calledUrl).toContain('customer_id=C1')
})

test('listOpsHiredAgentGoals builds URL with /pp/ops/hired-agents/{id}/goals', async () => {
  const { gatewayApiClient } = await import('../services/gatewayApiClient')
  fetchMock.mockResolvedValueOnce(
    new Response(JSON.stringify({}), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    })
  )
  await gatewayApiClient.listOpsHiredAgentGoals('inst-1', { customer_id: 'C1' })
  expect(fetchMock).toHaveBeenCalledTimes(1)
  const calledUrl: string = fetchMock.mock.calls[0][0] as string
  expect(calledUrl).toContain('/pp/ops/hired-agents/inst-1/goals')
  expect(calledUrl).toContain('customer_id=C1')
})

test('listOpsHiredAgentDeliverables builds URL with /pp/ops/hired-agents/{id}/deliverables', async () => {
  const { gatewayApiClient } = await import('../services/gatewayApiClient')
  fetchMock.mockResolvedValueOnce(
    new Response(JSON.stringify({}), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    })
  )
  await gatewayApiClient.listOpsHiredAgentDeliverables('inst-1', { customer_id: 'C1' })
  expect(fetchMock).toHaveBeenCalledTimes(1)
  const calledUrl: string = fetchMock.mock.calls[0][0] as string
  expect(calledUrl).toContain('/pp/ops/hired-agents/inst-1/deliverables')
})
