import '@testing-library/jest-dom/vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { expect, test, vi } from 'vitest'

import AgentSetup from './AgentSetup'

const mocks = vi.hoisted(() => {
  return {
    listAgentSetups: vi.fn(async () => ({
      count: 1,
      setups: [
        {
          customer_id: 'CUST-001',
          agent_id: 'AGT-MKT-HEALTH-001',
          channels: ['linkedin'],
          posting_identity: 'Care Clinic',
          credential_refs: { linkedin: 'credref-link-1' },
          updated_at: '2026-02-06T00:00:00Z'
        }
      ]
    })),
    upsertAgentSetup: vi.fn(async () => ({ updated_at: '2026-02-06T00:00:01Z' }))
  }
})

vi.mock('../services/gatewayApiClient', () => {
  return vi.importActual<any>('../services/gatewayApiClient').then((actual) => {
    return {
      ...actual,
      gatewayApiClient: {
        ...(actual.gatewayApiClient || {}),
        listAgentSetups: mocks.listAgentSetups,
        upsertAgentSetup: mocks.upsertAgentSetup
      }
    }
  })
})

test('AgentSetup loads and saves via API client', async () => {
  render(<AgentSetup />)

  expect(screen.getByText('Agent Setup')).toBeInTheDocument()

  fireEvent.click(screen.getByRole('button', { name: 'Load' }))

  await waitFor(() => {
    expect(mocks.listAgentSetups).toHaveBeenCalledTimes(1)
  })

  fireEvent.click(screen.getByRole('button', { name: 'Save' }))

  await waitFor(() => {
    expect(mocks.upsertAgentSetup).toHaveBeenCalledTimes(1)
  })

  expect(mocks.upsertAgentSetup.mock.calls[0][0]).toMatchObject({
    customer_id: 'CUST-001',
    agent_id: 'AGT-MKT-HEALTH-001'
  })
})
