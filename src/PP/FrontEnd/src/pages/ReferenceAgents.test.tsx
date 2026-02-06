import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { expect, test, vi } from 'vitest'

import ReferenceAgents from './ReferenceAgents'

vi.mock('../services/gatewayApiClient', () => {
  return {
    gatewayApiClient: {
      listReferenceAgents: vi.fn(async () => [
        {
          agent_id: 'AGT-MKT-CAKE-001',
          display_name: 'Cake Shop Marketing Agent',
          agent_type: 'marketing',
          spec: { version: '1.0' }
        }
      ])
    }
  }
})

test('ReferenceAgents renders list from API', async () => {
  render(<ReferenceAgents />)

  await waitFor(() => {
    expect(screen.getByText('Available Agents (1)')).toBeInTheDocument()
  })

  expect(screen.getByText('Cake Shop Marketing Agent')).toBeInTheDocument()
  expect(screen.getByText(/AGT-MKT-CAKE-001/)).toBeInTheDocument()
})
