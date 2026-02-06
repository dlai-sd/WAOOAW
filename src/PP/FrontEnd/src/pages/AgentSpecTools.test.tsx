import '@testing-library/jest-dom/vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, test, vi } from 'vitest'

import AgentSpecTools from './AgentSpecTools'
import { GatewayApiError } from '../services/gatewayApiClient'

function stubClipboard(): void {
  Object.defineProperty(globalThis.navigator, 'clipboard', {
    value: { writeText: vi.fn(async () => undefined) },
    configurable: true
  })
}

const mocks = vi.hoisted(() => {
  return {
    fetchAgentSpecSchema: vi.fn(async () => ({
      $schema: 'http://json-schema.org/draft-07/schema#',
      title: 'AgentSpec'
    })),
    validateAgentSpec: vi.fn(async () => ({ valid: true }))
  }
})

beforeEach(() => {
  vi.clearAllMocks()
})

vi.mock('../services/gatewayApiClient', () => {
  return vi.importActual<any>('../services/gatewayApiClient').then((actual) => {
    return {
      ...actual,
      gatewayApiClient: {
        ...(actual.gatewayApiClient || {}),
        fetchAgentSpecSchema: mocks.fetchAgentSpecSchema,
        validateAgentSpec: mocks.validateAgentSpec
      }
    }
  })
})

test('AgentSpecTools loads and renders schema JSON', async () => {
  stubClipboard()

  render(<AgentSpecTools />)

  await waitFor(() => {
    expect(mocks.fetchAgentSpecSchema).toHaveBeenCalledTimes(1)
  })

  await waitFor(() => {
    expect(screen.getByText('AgentSpec JSON Schema')).toBeInTheDocument()
  })

  expect(screen.getByText(/\"title\": \"AgentSpec\"/)).toBeInTheDocument()
})

test('AgentSpecTools validates a spec and shows valid=true', async () => {
  const user = userEvent.setup()
  stubClipboard()

  render(<AgentSpecTools />)

  await waitFor(() => {
    expect(mocks.fetchAgentSpecSchema).toHaveBeenCalledTimes(1)
  })

  fireEvent.change(screen.getByPlaceholderText(/agent_id/i), {
    target: { value: '{"agent_id":"AGT-1","display_name":"Demo","agent_type":"marketing","dimensions":[]}' }
  })
  await user.click(screen.getByRole('button', { name: 'Validate' }))

  await waitFor(() => {
    expect(mocks.validateAgentSpec).toHaveBeenCalledTimes(1)
  })

  expect(screen.getByText('Valid: true')).toBeInTheDocument()
})

test('AgentSpecTools surfaces 422 violations in the error panel', async () => {
  const user = userEvent.setup()
  stubClipboard()

  mocks.validateAgentSpec.mockRejectedValueOnce(
    new GatewayApiError('Request Validation Error', {
      status: 422,
      correlationId: 'corr-422',
      problem: {
        title: 'Request Validation Error',
        detail: 'invalid spec',
        correlation_id: 'corr-422',
        violations: [{ loc: ['body', 'agent_id'], msg: 'field required', type: 'missing' }]
      } as any
    })
  )

  render(<AgentSpecTools />)

  await waitFor(() => {
    expect(mocks.fetchAgentSpecSchema).toHaveBeenCalledTimes(1)
  })

  fireEvent.change(screen.getByPlaceholderText(/agent_id/i), {
    target: { value: '{"not":"a spec"}' }
  })
  await user.click(screen.getByRole('button', { name: 'Validate' }))

  await waitFor(() => {
    expect(screen.getByText(/422:/)).toBeInTheDocument()
  })

  expect(screen.getByText(/Correlation: corr-422/)).toBeInTheDocument()
  expect(screen.getByText(/"loc"/)).toBeInTheDocument()
})
