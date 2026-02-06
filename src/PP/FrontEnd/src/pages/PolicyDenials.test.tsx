import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, test, vi } from 'vitest'

import PolicyDenials from './PolicyDenials'

const mocks = vi.hoisted(() => {
  return {
    listPolicyDenials: vi.fn(async () => ({
      count: 1,
      records: [
        {
          created_at: '2026-02-06T00:00:00Z',
          correlation_id: 'corr-abc',
          decision_id: 'dec-1',
          action: 'publish',
          reason: 'approval_required',
          path: '/api/v1/reference-agents/AGT-1/run',
          details: {
            missing: 'approval_id'
          }
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
        listPolicyDenials: mocks.listPolicyDenials
      }
    }
  })
})

test('PolicyDenials renders policy denial records from API', async () => {
  const user = userEvent.setup()
  render(<PolicyDenials />)

  await waitFor(() => {
    expect(screen.getByText('Policy Denials')).toBeInTheDocument()
  })

  await waitFor(() => {
    expect(mocks.listPolicyDenials).toHaveBeenCalledTimes(1)
  })

  expect(mocks.listPolicyDenials).toHaveBeenCalledWith({
    correlation_id: undefined,
    customer_id: undefined,
    agent_id: undefined,
    limit: 100
  })

  await waitFor(() => {
    expect(screen.getByText('corr-abc')).toBeInTheDocument()
  })

  expect(screen.getByText('approval_required')).toBeInTheDocument()
  expect(screen.getByText('dec-1')).toBeInTheDocument()

  await user.click(screen.getByText('corr-abc'))
  expect(screen.getByText('Denial Details')).toBeInTheDocument()
  expect(screen.getByText(/Recommended next action: Provide approval_id and retry the action\./)).toBeInTheDocument()
  expect(screen.getByText(/"missing": "approval_id"/)).toBeInTheDocument()
})
