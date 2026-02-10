import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { expect, test, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'

import AgentManagement from './AgentManagement'

const mocks = vi.hoisted(() => {
  return {
    listAgents: vi.fn(async () => []),
    listAgentTypeDefinitions: vi.fn(async () => [
      { agent_type_id: 'marketing.healthcare.v1', version: '1.0.0' }
    ]),
    getAgentTypeDefinition: vi.fn(async () => ({ agent_type_id: 'marketing.healthcare.v1', version: '1.0.0', config_schema: { fields: [] }, goal_templates: [], enforcement_defaults: { approval_required: true, deterministic: false } })),
    publishAgentTypeDefinition: vi.fn(async (_id: string, payload: any) => payload)
  }
})

vi.mock('../services/gatewayApiClient', () => {
  return vi.importActual<any>('../services/gatewayApiClient').then((actual) => {
    return {
      ...actual,
      gatewayApiClient: {
        ...(actual.gatewayApiClient || {}),
        listAgents: mocks.listAgents,
        listAgentTypeDefinitions: mocks.listAgentTypeDefinitions,
        getAgentTypeDefinition: mocks.getAgentTypeDefinition,
        publishAgentTypeDefinition: mocks.publishAgentTypeDefinition
      }
    }
  })
})

test('AgentManagement loads and publishes agent type definitions', async () => {
  render(
    <MemoryRouter>
      <AgentManagement />
    </MemoryRouter>
  )

  await waitFor(() => {
    expect(mocks.listAgents).toHaveBeenCalledTimes(1)
    expect(mocks.listAgentTypeDefinitions).toHaveBeenCalledTimes(1)
  })

  expect(await screen.findByText('marketing.healthcare.v1')).toBeInTheDocument()

  fireEvent.click(screen.getByRole('button', { name: 'Edit' }))

  await waitFor(() => {
    expect(mocks.getAgentTypeDefinition).toHaveBeenCalledTimes(1)
  })

  fireEvent.click(screen.getByRole('button', { name: 'Publish' }))

  await waitFor(() => {
    expect(mocks.publishAgentTypeDefinition).toHaveBeenCalledTimes(1)
  })
})
