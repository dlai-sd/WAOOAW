import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { beforeEach, expect, test, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'

import AgentManagement from './AgentManagement'

function makeDraft(overrides: Record<string, unknown> = {}) {
  return {
    draft_id: 'draft-dma-1',
    candidate_agent_type_id: 'marketing.digital_marketing.v1',
    candidate_agent_label: 'Digital Marketing Agent',
    contract_payload: {},
    section_states: {
      define_agent: 'ready',
      operating_contract: 'ready',
      deliverables: 'ready',
      governance: 'ready',
    },
    constraint_policy: {},
    reviewer_comments: [],
    status: 'draft',
    reviewer_id: null,
    reviewer_name: null,
    submitted_at: null,
    reviewed_at: null,
    created_at: '2026-03-14T09:00:00Z',
    updated_at: '2026-03-14T10:00:00Z',
    ...overrides,
  }
}

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
    listAgentAuthoringDrafts: vi.fn(async () => [makeDraft()]),
    submitAgentAuthoringDraft: vi.fn(async (_draftId: string) => makeDraft({ draft_id: _draftId, status: 'in_review', submitted_at: '2026-03-14T10:15:00Z' })),
    requestAgentAuthoringChanges: vi.fn(async (_draftId: string, payload: any) => makeDraft({
      draft_id: _draftId,
      status: 'changes_requested',
      reviewer_name: payload.reviewer_name || 'PP Review Board',
      reviewer_comments: payload.reviewer_comments,
      reviewed_at: '2026-03-14T10:20:00Z'
    })),
    approveAgentAuthoringDraft: vi.fn(async (_draftId: string, payload: any) => makeDraft({
      draft_id: _draftId,
      status: 'approved',
      reviewer_name: payload.reviewer_name || 'PP Review Board',
      reviewed_at: '2026-03-14T10:30:00Z'
    })),
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
        listAgentAuthoringDrafts: mocks.listAgentAuthoringDrafts,
        submitAgentAuthoringDraft: mocks.submitAgentAuthoringDraft,
        requestAgentAuthoringChanges: mocks.requestAgentAuthoringChanges,
        approveAgentAuthoringDraft: mocks.approveAgentAuthoringDraft,
        listAgentTypeDefinitions: mocks.listAgentTypeDefinitions,
        getAgentTypeDefinition: mocks.getAgentTypeDefinition,
        publishAgentTypeDefinition: mocks.publishAgentTypeDefinition
      }
    }
  })
})

beforeEach(() => {
  vi.clearAllMocks()
  mocks.listAgents.mockResolvedValue([
    { id: 'AGT-MKT-001', name: 'Digital Marketing Agent', industry: 'marketing', status: 'active' }
  ])
  mocks.listCatalogReleases.mockResolvedValue([
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
  ])
  mocks.listAgentAuthoringDrafts.mockResolvedValue([makeDraft()])
  mocks.submitAgentAuthoringDraft.mockImplementation(async (_draftId: string) => makeDraft({ draft_id: _draftId, status: 'in_review', submitted_at: '2026-03-14T10:15:00Z' }))
  mocks.requestAgentAuthoringChanges.mockImplementation(async (_draftId: string, payload: any) => makeDraft({
    draft_id: _draftId,
    status: 'changes_requested',
    reviewer_name: payload.reviewer_name || 'PP Review Board',
    reviewer_comments: payload.reviewer_comments,
    reviewed_at: '2026-03-14T10:20:00Z'
  }))
  mocks.approveAgentAuthoringDraft.mockImplementation(async (_draftId: string, payload: any) => makeDraft({
    draft_id: _draftId,
    status: 'approved',
    reviewer_name: payload.reviewer_name || 'PP Review Board',
    reviewed_at: '2026-03-14T10:30:00Z'
  }))
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
    expect(mocks.listAgentAuthoringDrafts).toHaveBeenCalledTimes(1)
    expect(mocks.listAgentTypeDefinitions).toHaveBeenCalledTimes(1)
  })

  expect(await screen.findByText('Base Agent Contract Review Board')).toBeInTheDocument()
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

test('AgentManagement submits a draft for review and shows reviewer next-step guidance', async () => {
  render(
    <MemoryRouter>
      <AgentManagement />
    </MemoryRouter>
  )

  expect(await screen.findByText('Base Agent Contract Review Board')).toBeInTheDocument()

  fireEvent.click(screen.getByRole('button', { name: 'Submit for review' }))

  await waitFor(() => {
    expect(mocks.submitAgentAuthoringDraft).toHaveBeenCalledWith('draft-dma-1')
  })

  expect(screen.getByTestId('agent-authoring-next-step')).toHaveTextContent('Draft submitted for review')
})

test('AgentManagement captures section-tied feedback when requesting changes', async () => {
  mocks.listAgentAuthoringDrafts.mockResolvedValueOnce([
    makeDraft({ status: 'in_review', submitted_at: '2026-03-14T10:15:00Z' })
  ])

  render(
    <MemoryRouter>
      <AgentManagement />
    </MemoryRouter>
  )

  expect(await screen.findByText('Base Agent Contract Review Board')).toBeInTheDocument()

  fireEvent.change(screen.getByLabelText('Reviewer feedback'), {
    target: { value: 'Clarify the buyer promise before approval.' }
  })
  fireEvent.click(screen.getByRole('button', { name: 'Request changes' }))

  await waitFor(() => {
    expect(mocks.requestAgentAuthoringChanges).toHaveBeenCalledWith(
      'draft-dma-1',
      expect.objectContaining({
        reviewer_name: 'PP Review Board',
        reviewer_comments: [
          expect.objectContaining({
            section_key: 'define_agent',
            comment: 'Clarify the buyer promise before approval.',
            severity: 'changes_requested'
          })
        ]
      })
    )
  })

  expect(screen.getByTestId('agent-authoring-next-step')).toHaveTextContent('Return path')
  expect(screen.getByText('Clarify the buyer promise before approval.')).toBeInTheDocument()
})

test('AgentManagement approves a reviewed draft and shows catalog-preparation next step', async () => {
  mocks.listAgentAuthoringDrafts.mockResolvedValueOnce([
    makeDraft({ status: 'in_review', submitted_at: '2026-03-14T10:15:00Z' })
  ])

  render(
    <MemoryRouter>
      <AgentManagement />
    </MemoryRouter>
  )

  expect(await screen.findByText('Base Agent Contract Review Board')).toBeInTheDocument()

  fireEvent.click(screen.getByRole('button', { name: 'Approve contract' }))

  await waitFor(() => {
    expect(mocks.approveAgentAuthoringDraft).toHaveBeenCalledWith(
      'draft-dma-1',
      expect.objectContaining({ reviewer_name: 'PP Review Board' })
    )
  })

  expect(screen.getByTestId('agent-authoring-next-step')).toHaveTextContent('ready for catalog preparation')
})
