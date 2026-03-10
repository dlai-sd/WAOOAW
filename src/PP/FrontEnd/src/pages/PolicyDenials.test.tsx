import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { expect, test, vi } from 'vitest'

import PolicyDenials from './PolicyDenials'

function LocationEcho() {
  const location = useLocation()
  return <div data-testid="location-display">{`${location.pathname}${location.search}`}</div>
}

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
  render(
    <MemoryRouter initialEntries={['/policy-denials']}>
      <Routes>
        <Route path="/policy-denials" element={<PolicyDenials />} />
      </Routes>
    </MemoryRouter>
  )

  await waitFor(() => {
    expect(screen.getByText('Policy Denials')).toBeInTheDocument()
  })

   expect(mocks.listPolicyDenials).not.toHaveBeenCalled()

  await user.click(screen.getByRole('button', { name: 'Load denials' }))

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

test('PolicyDenials auto-loads handoff filters and links to hired runtime', async () => {
  const user = userEvent.setup()

  render(
    <MemoryRouter initialEntries={['/policy-denials?customer_id=CUST-1&agent_id=AGT-1&correlation_id=corr-abc']}>
      <Routes>
        <Route path="/policy-denials" element={<PolicyDenials />} />
        <Route path="/hired-agents" element={<LocationEcho />} />
      </Routes>
    </MemoryRouter>
  )

  await waitFor(() => {
    expect(mocks.listPolicyDenials).toHaveBeenCalledWith({
      correlation_id: 'corr-abc',
      customer_id: 'CUST-1',
      agent_id: 'AGT-1',
      limit: 100
    })
  })

  expect(screen.getByText('Operator handoff context')).toBeInTheDocument()

  await user.click(screen.getByText('corr-abc'))
  await user.click(screen.getByRole('button', { name: 'Open hired agent runtime' }))

  await waitFor(() => {
    expect(screen.getByTestId('location-display')).toHaveTextContent('/hired-agents?')
    expect(screen.getByTestId('location-display')).toHaveTextContent('customer_id=CUST-1')
    expect(screen.getByTestId('location-display')).toHaveTextContent('agent_id=AGT-1')
    expect(screen.getByTestId('location-display')).toHaveTextContent('correlation_id=corr-abc')
  })
})
