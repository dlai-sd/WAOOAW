import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { expect, test, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'

import AgentManagement from './AgentManagement'

const mocks = vi.hoisted(() => {
  return {
    listAgents: vi.fn(async () => [
      { id: 'AGT-MKT-001', name: 'Digital Marketing Agent', industry: 'marketing', status: 'active' }
    ]),
    listCatalogReleases: vi.fn(async () => [
      {
        release_id: 'CAR-1',
        id: 'AGT-MKT-001',
        public_name: 'Digital Marketing Agent',
        short_description: 'Hire-ready release',
        industry_name: 'Marketing',
        job_role_label: 'Digital Marketer',
        monthly_price_inr: 12000,
        trial_days: 7,
        allowed_durations: ['monthly', 'quarterly'],
        supported_channels: ['youtube'],
        approval_mode: 'manual_review',
        agent_type_id: 'marketing.digital_marketing.v1',
        internal_definition_version_id: '1.0.0',
        external_catalog_version: 'v1',
        lifecycle_state: 'draft',
        approved_for_new_hire: false,
        retired_from_catalog_at: null,
      }
    ]),
    upsertCatalogRelease: vi.fn(async (_id: string, payload: any) => ({ release_id: 'CAR-1', id: _id, ...payload })),
    approveCatalogRelease: vi.fn(async (_id: string) => ({ release_id: 'CAR-1', id: _id, lifecycle_state: 'live_on_cp' })),
    retireCatalogRelease: vi.fn(async (_releaseId: string) => ({ release_id: _releaseId, lifecycle_state: 'retired_from_catalog' })),
    listAgentTypeDefinitions: vi.fn(async () => [
      { agent_type_id: 'marketing.healthcare.v1', version: '1.0.0' }
    ]),
    getAgentTypeDefinition: vi.fn(async () => ({ agent_type_id: 'marketing.healthcare.v1', version: '1.0.0', required_skill_keys: ['content_strategy'], config_schema: { fields: [] }, goal_templates: [], enforcement_defaults: { approval_required: true, deterministic: false } })),
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
        listCatalogReleases: mocks.listCatalogReleases,
        upsertCatalogRelease: mocks.upsertCatalogRelease,
        approveCatalogRelease: mocks.approveCatalogRelease,
        retireCatalogRelease: mocks.retireCatalogRelease,
        listAgentTypeDefinitions: mocks.listAgentTypeDefinitions,
        getAgentTypeDefinition: mocks.getAgentTypeDefinition,
        publishAgentTypeDefinition: mocks.publishAgentTypeDefinition
      }
    }
  })
})

test('AgentManagement loads release board and publishes agent type definitions', async () => {
  render(
    <MemoryRouter>
      <AgentManagement />
    </MemoryRouter>
  )

  await waitFor(() => {
    expect(mocks.listAgents).toHaveBeenCalledTimes(1)
    expect(mocks.listCatalogReleases).toHaveBeenCalledTimes(1)
    expect(mocks.listAgentTypeDefinitions).toHaveBeenCalledTimes(1)
  })

  expect(await screen.findByText('Digital Marketing Agent Release Board')).toBeInTheDocument()
  expect(await screen.findByDisplayValue('Digital Marketing Agent')).toBeInTheDocument()

  fireEvent.click(screen.getByRole('button', { name: 'Approve for CP' }))

  await waitFor(() => {
    expect(mocks.approveCatalogRelease).toHaveBeenCalledWith('AGT-MKT-001')
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

test('AgentManagement saves and retires a catalog release', async () => {
  render(
    <MemoryRouter>
      <AgentManagement />
    </MemoryRouter>
  )

  expect(await screen.findByDisplayValue('Digital Marketing Agent')).toBeInTheDocument()

  await waitFor(() => {
    expect(screen.getByRole('button', { name: 'Save release' })).toBeEnabled()
  })

  fireEvent.click(screen.getByRole('button', { name: 'Save release' }))

  await waitFor(() => {
    expect(mocks.upsertCatalogRelease).toHaveBeenCalledTimes(1)
  })

  await waitFor(() => {
    expect(mocks.listCatalogReleases.mock.calls.length).toBeGreaterThanOrEqual(2)
  })

  fireEvent.click(screen.getByRole('button', { name: 'Retire from catalog' }))

  await waitFor(() => {
    expect(mocks.retireCatalogRelease).toHaveBeenCalledWith('CAR-1')
  })
})
