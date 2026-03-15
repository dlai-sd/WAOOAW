import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, test, vi } from 'vitest'

import AgentTypeSetupScreen from '../pages/AgentTypeSetupScreen'

const mocks = vi.hoisted(() => ({
  gatewayRequestJson: vi.fn(async () => []),
}))

vi.mock('../services/gatewayApiClient', () => ({
  gatewayRequestJson: mocks.gatewayRequestJson,
  GatewayApiError: class GatewayApiError extends Error {},
}))

function installDefaultGatewayMock() {
  mocks.gatewayRequestJson.mockImplementation(async (path: string, init?: RequestInit) => {
    if (String(path).includes('processors') || String(path).includes('pumps')) return []
    if (String(path).includes('/pp/agent-authoring/drafts/') && (!init || !init.method || init.method === 'GET')) {
      return {
        draft_id: 'AAD-1',
        candidate_agent_type_id: 'marketing.digital_marketing_agent',
        candidate_agent_label: 'Digital Marketing Agent',
        contract_payload: {
          identity: {
            description: 'Runs approved digital marketing work with a clear human review path.',
            industry: 'marketing',
            target_customer: 'Growth-stage business that needs a dependable digital marketing operator.',
          },
          operating_contract: {
            processor_class: 'ContentProcessor',
            pump_class: 'SocialMediaPump',
            approval_mode: 'manual',
            max_tasks_per_day: 10,
            max_position_size_inr: 0,
            trial_task_limit: 10,
          },
          deliverables: {
            primary_outcomes: 'Publish clear campaign deliverables.',
            deliverable_commitments: 'Weekly plans and channel-ready assets.',
            optional_extensions: '',
          },
          governance: {
            handoff_notes: 'Confirm review queue and next owner.',
            hooks: { AuditHook: true },
          },
        },
        section_states: {
          define_agent: 'ready',
          operating_contract: 'ready',
          deliverables: 'ready',
          governance: 'ready',
        },
        constraint_policy: { approval_required: true },
        reviewer_comments: [],
        status: 'draft',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
    }
    if (String(path) === '/pp/agent-authoring/drafts' && init?.method === 'POST') {
      return {
        draft_id: 'AAD-1',
        candidate_agent_type_id: 'marketing.digital_marketing_agent',
        candidate_agent_label: 'Digital Marketing Agent',
        contract_payload: {},
        section_states: {
          define_agent: 'ready',
          operating_contract: 'ready',
          deliverables: 'ready',
          governance: 'ready',
        },
        constraint_policy: { approval_required: true },
        reviewer_comments: [],
        status: 'draft',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
    }
    if (String(path).endsWith('/submit')) {
      return {
        draft_id: 'AAD-1',
        candidate_agent_type_id: 'marketing.digital_marketing_agent',
        candidate_agent_label: 'Digital Marketing Agent',
        contract_payload: {},
        section_states: {
          define_agent: 'ready',
          operating_contract: 'ready',
          deliverables: 'ready',
          governance: 'ready',
        },
        constraint_policy: { approval_required: true },
        reviewer_comments: [],
        status: 'in_review',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
    }
    return []
  })
}

test('AgentTypeSetupScreen renders the new studio shell and template choices', () => {
  installDefaultGatewayMock()
  render(<AgentTypeSetupScreen />)

  expect(screen.getByText('Agent Setup Studio')).toBeInTheDocument()
  expect(screen.getAllByText('Choose a starting point').length).toBeGreaterThan(0)
  expect(screen.getByRole('button', { name: /Digital Marketing Agent/i })).toBeInTheDocument()
})

test('AgentTypeSetupScreen moves into identity authoring after continue', async () => {
  installDefaultGatewayMock()
  const user = userEvent.setup()
  render(<AgentTypeSetupScreen />)

  await user.click(screen.getByRole('button', { name: 'Continue' }))

  expect(screen.getByLabelText(/Agent display name/i)).toBeInTheDocument()
  expect(screen.getByDisplayValue('Digital Marketing Agent')).toBeInTheDocument()
  expect(screen.getByText('Primary industry')).toBeInTheDocument()
})

test('AgentTypeSetupScreen hides advanced runtime mapping until requested', async () => {
  installDefaultGatewayMock()
  const user = userEvent.setup()
  render(<AgentTypeSetupScreen />)

  await user.click(screen.getByRole('button', { name: /Set operating rules/i }))

  expect(screen.queryByLabelText(/Processor class/i)).not.toBeInTheDocument()
  await user.click(screen.getByRole('checkbox', { name: /Show processor, pump, and integration classes/i }))
  expect(screen.getByLabelText(/Processor class/i)).toBeInTheDocument()
  expect(screen.getByLabelText(/Pump class/i)).toBeInTheDocument()
})

test('AgentTypeSetupScreen keeps submit disabled until mandatory sections are complete', async () => {
  installDefaultGatewayMock()
  const user = userEvent.setup()
  render(<AgentTypeSetupScreen />)

  await user.click(screen.getByRole('button', { name: /Prepare for review/i }))

  expect(screen.getByRole('button', { name: 'Submit for review' })).toBeDisabled()
})

test('AgentTypeSetupScreen shows unsaved changes then saved message after saving', async () => {
  installDefaultGatewayMock()
  const user = userEvent.setup()
  render(<AgentTypeSetupScreen />)

  await user.click(screen.getByRole('button', { name: /Shape customer value/i }))
  await user.type(screen.getByLabelText(/Primary customer outcomes/i), 'Publish channel-ready content.')
  expect(screen.getAllByText('Unsaved changes').length).toBeGreaterThan(0)

  await user.click(screen.getByRole('button', { name: 'Save draft' }))

  await waitFor(() => {
    expect(screen.getAllByText(/Draft saved at/i).length).toBeGreaterThan(0)
  })
})

test('AgentTypeSetupScreen shows recovery messaging and preserves inputs on save failure', async () => {
  mocks.gatewayRequestJson.mockImplementation(async (path: string, init?: RequestInit) => {
    if (String(path).includes('processors') || String(path).includes('pumps')) return []
    if (String(path) === '/pp/agent-authoring/drafts' && init?.method === 'POST') {
      throw new Error('network down')
    }
    return []
  })

  const user = userEvent.setup()
  render(<AgentTypeSetupScreen />)

  await user.click(screen.getByRole('button', { name: /Shape customer value/i }))
  const outcomes = screen.getByLabelText(/Primary customer outcomes/i)
  await user.type(outcomes, 'Keep this text on screen.')
  await user.click(screen.getByRole('button', { name: 'Save draft' }))

  await waitFor(() => {
    expect(screen.getAllByText('Save failed. Your draft stays on screen. Check the connection and try again.').length).toBeGreaterThan(0)
  })
  expect(screen.getByDisplayValue('Keep this text on screen.')).toBeInTheDocument()
})

test('AgentTypeSetupScreen warns on beforeunload when there are unsaved changes', async () => {
  installDefaultGatewayMock()
  const user = userEvent.setup()
  render(<AgentTypeSetupScreen />)

  await user.click(screen.getByRole('button', { name: /Shape customer value/i }))
  await user.type(screen.getByLabelText(/Primary customer outcomes/i), 'Unsaved contract state.')

  const event = new Event('beforeunload', { cancelable: true })
  Object.defineProperty(event, 'returnValue', { writable: true, value: '' })
  window.dispatchEvent(event)

  expect(event.defaultPrevented).toBe(true)
})

test('AgentTypeSetupScreen loads an existing draft in edit mode', async () => {
  installDefaultGatewayMock()
  render(<AgentTypeSetupScreen agentSetupId="setup-123" />)

  await waitFor(() => {
    expect(screen.getByDisplayValue('Digital Marketing Agent')).toBeInTheDocument()
  })
})

test('AgentTypeSetupScreen calls loadClassOptions on mount', async () => {
  installDefaultGatewayMock()
  render(<AgentTypeSetupScreen />)

  await waitFor(() => {
    expect(mocks.gatewayRequestJson).toHaveBeenCalled()
  })
})
