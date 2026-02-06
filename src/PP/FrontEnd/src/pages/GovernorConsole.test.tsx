import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { beforeEach, expect, test, vi } from 'vitest'

import GovernorConsole from './GovernorConsole'

const mocks = vi.hoisted(() => {
  return {
    listReferenceAgents: vi.fn(async () => [
      {
        agent_id: 'AGT-MKT-CAKE-001',
        display_name: 'Cake Shop Marketing Agent',
        agent_type: 'marketing',
        spec: { version: '1.0' }
      }
    ]),
    runReferenceAgent: vi.fn()
  }
})

vi.mock('../services/gatewayApiClient', () => {
  return vi.importActual<any>('../services/gatewayApiClient').then((actual) => {
    return {
      ...actual,
      gatewayApiClient: {
        ...(actual.gatewayApiClient || {}),
        listReferenceAgents: mocks.listReferenceAgents,
        runReferenceAgent: mocks.runReferenceAgent,
      },
    }
  })
})

beforeEach(() => {
  mocks.listReferenceAgents.mockClear()
  mocks.runReferenceAgent.mockClear()
})

test('GovernorConsole shows approval_required reason when publish denied', async () => {
  const { GatewayApiError } = await import('../services/gatewayApiClient')
  mocks.runReferenceAgent.mockRejectedValueOnce(
    new GatewayApiError('Policy denied tool use', {
      status: 403,
      correlationId: 'corr-1',
      problem: {
        title: 'Policy Enforcement Denied',
        detail: 'Policy denied tool use',
        reason: 'approval_required',
        details: { action: 'publish' },
        correlation_id: 'corr-1'
      }
    })
  )

  render(<GovernorConsole />)

  await waitFor(() => {
    expect(screen.getByText('Approval-assisted publish (Plant)')).toBeInTheDocument()
  })

  const button = screen.getByRole('button', { name: 'Attempt Publish' })
  fireEvent.click(button)

  await waitFor(() => {
    expect(screen.getByText(/Reason: approval_required/)).toBeInTheDocument()
  })
})

test('GovernorConsole shows published=true when approval is provided', async () => {
  mocks.runReferenceAgent.mockResolvedValueOnce({
    agent_id: 'AGT-MKT-CAKE-001',
    agent_type: 'marketing',
    status: 'published',
    review: { approval_id: 'APR-123' },
    draft: { ok: true },
    published: true,
  })

  render(<GovernorConsole />)

  await waitFor(() => {
    expect(screen.getByText('Approval-assisted publish (Plant)')).toBeInTheDocument()
  })

  const approvalInput = screen.getByPlaceholderText('APR-123')
  fireEvent.change(approvalInput, { target: { value: 'APR-123' } })

  const button = screen.getByRole('button', { name: 'Attempt Publish' })
  fireEvent.click(button)

  await waitFor(() => {
    expect(screen.getByText(/Published: true/)).toBeInTheDocument()
  })

  expect(mocks.runReferenceAgent).toHaveBeenCalledTimes(1)
  expect(mocks.runReferenceAgent.mock.calls[0]?.[0]).toBe('AGT-MKT-CAKE-001')
  const payload = mocks.runReferenceAgent.mock.calls[0]?.[1] as any
  expect(payload.do_publish).toBe(true)
  expect(payload.approval_id).toBe('APR-123')
})
