import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { expect, test, vi } from 'vitest'

import AgentSpecTools from './AgentSpecTools'

const mocks = vi.hoisted(() => {
  return {
    fetchAgentSpecSchema: vi.fn(async () => ({
      $schema: 'http://json-schema.org/draft-07/schema#',
      title: 'AgentSpec'
    }))
  }
})

vi.mock('../services/gatewayApiClient', () => {
  return vi.importActual<any>('../services/gatewayApiClient').then((actual) => {
    return {
      ...actual,
      gatewayApiClient: {
        ...(actual.gatewayApiClient || {}),
        fetchAgentSpecSchema: mocks.fetchAgentSpecSchema
      }
    }
  })
})

test('AgentSpecTools loads and renders schema JSON', async () => {
  ;(globalThis as any).navigator.clipboard = { writeText: vi.fn(async () => undefined) }

  render(<AgentSpecTools />)

  await waitFor(() => {
    expect(mocks.fetchAgentSpecSchema).toHaveBeenCalledTimes(1)
  })

  await waitFor(() => {
    expect(screen.getByText('AgentSpec JSON Schema')).toBeInTheDocument()
  })

  expect(screen.getByText(/\"title\": \"AgentSpec\"/)).toBeInTheDocument()
})
