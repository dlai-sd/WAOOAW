import '@testing-library/jest-dom/vitest'
import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { expect, test, vi } from 'vitest'

import HiredAgentsOps from './HiredAgentsOps'

function LocationEcho() {
  const location = useLocation()
  return <div data-testid="location-display">{`${location.pathname}${location.search}`}</div>
}

const mocks = vi.hoisted(() => {
  return {
    listOpsHiredAgents: vi.fn(async () => ([
      {
        hired_instance_id: 'HIRE-1',
        subscription_id: 'SUB-1',
        agent_id: 'AGT-MKT-HEALTH-001',
        configured: true,
        goals_completed: true,
        trial_status: 'active',
        config: { timezone: 'Asia/Kolkata' }
      }
    ])),
    listOpsHiredAgentGoals: vi.fn(async () => ({
      hired_instance_id: 'HIRE-1',
      goals: [
        {
          goal_instance_id: 'GOI-1',
          goal_template_id: 'marketing.daily_micro_post.v1',
          frequency: 'daily',
          settings: { platform: 'x' }
        }
      ]
    })),
    listOpsHiredAgentDeliverables: vi.fn(async () => ({
      hired_instance_id: 'HIRE-1',
      deliverables: [
        {
          deliverable_id: 'DEL-1',
          goal_template_id: 'marketing.daily_micro_post.v1',
          frequency: 'daily',
          review_status: 'draft',
          approval_id: null,
          execution_status: null,
          created_at: '2026-02-10T00:00:00Z'
        }
      ]
    })),
    listOpsHiredAgentSkills: vi.fn(async () => ([])),
    listOpsPlatformConnections: vi.fn(async () => ([])),
    listApprovals: vi.fn(async () => ({
      count: 1,
      approvals: [
        {
          approval_id: 'APR-1',
          customer_id: 'CUST-1',
          agent_id: 'AGT-MKT-HEALTH-001',
          action: 'publish',
          correlation_id: 'corr-1',
          created_at: '2026-02-10T00:00:00Z',
          expires_at: null
        }
      ]
    })),
    listPolicyDenials: vi.fn(async () => ({
      count: 1,
      records: [
        {
          created_at: '2026-02-10T00:00:00Z',
          correlation_id: 'corr-1',
          decision_id: 'DEC-1',
          agent_id: 'AGT-MKT-HEALTH-001',
          customer_id: 'CUST-1',
          action: 'publish',
          reason: 'approval_required',
          path: '/api/v1/deliverables/DEL-1/execute',
          details: { message: 'missing approval_id' }
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
        listOpsHiredAgents: mocks.listOpsHiredAgents,
        listOpsHiredAgentGoals: mocks.listOpsHiredAgentGoals,
        listOpsHiredAgentDeliverables: mocks.listOpsHiredAgentDeliverables,
        listOpsHiredAgentSkills: mocks.listOpsHiredAgentSkills,
        listOpsPlatformConnections: mocks.listOpsPlatformConnections,
        listApprovals: mocks.listApprovals,
        listPolicyDenials: mocks.listPolicyDenials
      }
    }
  })
})

test('HiredAgentsOps loads instances and renders drilldown sections', async () => {
  const user = userEvent.setup()
  render(
    <MemoryRouter initialEntries={['/hired-agents']}>
      <Routes>
        <Route path="/hired-agents" element={React.createElement(HiredAgentsOps as any) as any} />
      </Routes>
    </MemoryRouter>
  )

  await waitFor(() => {
    expect(screen.getByText('Hired Agents')).toBeInTheDocument()
  })

  await user.type(screen.getByLabelText('Customer ID'), 'CUST-1')
  await user.click(screen.getByRole('button', { name: 'Load' }))

  await waitFor(() => {
    expect(mocks.listOpsHiredAgents).toHaveBeenCalledWith(
      expect.objectContaining({ customer_id: 'CUST-1' })
    )
  })

  await waitFor(() => {
    expect(screen.getByText('HIRE-1')).toBeInTheDocument()
  })

  await user.click(screen.getByText('HIRE-1'))

  await waitFor(() => {
    expect(mocks.listOpsHiredAgentDeliverables).toHaveBeenCalledTimes(1)
    expect(mocks.listApprovals).toHaveBeenCalledTimes(1)
    expect(mocks.listPolicyDenials).toHaveBeenCalledTimes(1)
  })

  expect(screen.getByText('Drafts (Deliverables)')).toBeInTheDocument()
  expect(screen.getByText('DEL-1')).toBeInTheDocument()
  expect(screen.getAllByText('Approvals').length).toBeGreaterThan(0)
  expect(screen.getByText('APR-1')).toBeInTheDocument()
  expect(screen.getByText('Policy Denials')).toBeInTheDocument()
  expect(screen.getByText('approval_required')).toBeInTheDocument()
})

test('HiredAgentsOps surfaces DMA publish state without pretending approval implies publish', async () => {
  mocks.listOpsHiredAgents.mockResolvedValueOnce([
    {
      hired_instance_id: 'HIRE-9',
      subscription_id: 'SUB-9',
      agent_id: 'AGT-MKT-DMA-001',
      agent_type_id: 'marketing.digital_marketing.v1',
      configured: true,
      goals_completed: true,
      trial_status: 'active',
      config: { timezone: 'Asia/Kolkata' }
    }
  ])
  mocks.listOpsHiredAgentGoals.mockResolvedValueOnce({ hired_instance_id: 'HIRE-9', goals: [] })
  mocks.listOpsHiredAgentDeliverables.mockResolvedValueOnce({
    hired_instance_id: 'HIRE-9',
    deliverables: [
      {
        deliverable_id: 'DEL-9',
        review_status: 'approved',
        execution_status: 'scheduled',
        approval_id: 'APR-9',
        created_at: '2026-03-11T10:00:00Z',
        payload: {
          destination: { destination_type: 'youtube', metadata: { visibility: 'private' } },
          publish_status: 'not_published'
        }
      }
    ]
  })
  mocks.listOpsHiredAgentSkills.mockResolvedValueOnce([
    {
      skill_id: 'skill-theme-discovery',
      display_name: 'Theme Discovery',
      goal_schema: { fields: [{ key: 'business_name', label: 'Business name', required: true }] },
      goal_config: { business_name: 'WAOOAW Studio' }
    }
  ])
  mocks.listOpsPlatformConnections.mockResolvedValueOnce([])
  mocks.listApprovals.mockResolvedValueOnce({ count: 0, approvals: [] })
  mocks.listPolicyDenials.mockResolvedValueOnce({ count: 0, records: [] })

  const user = userEvent.setup()
  render(
    <MemoryRouter initialEntries={['/hired-agents']}>
      <Routes>
        <Route path="/hired-agents" element={React.createElement(HiredAgentsOps as any) as any} />
      </Routes>
    </MemoryRouter>
  )

  await user.type(screen.getByLabelText('Customer ID'), 'CUST-9')
  await user.click(screen.getByRole('button', { name: 'Load' }))

  await waitFor(() => {
    expect(screen.getByText('HIRE-9')).toBeInTheDocument()
  })

  await user.click(screen.getByText('HIRE-9'))

  await waitFor(() => {
    expect(screen.getByTestId('pp-dma-publish-readiness')).toHaveTextContent('Blocked by channel connection')
  })

  expect(screen.getByText('WAOOAW Studio')).toBeInTheDocument()
  expect(screen.getByTestId('pp-dma-channel-status')).toHaveTextContent('Youtube not connected')
})

test('HiredAgentsOps preserves handoff context and links to the next operator surface', async () => {
  const user = userEvent.setup()

  render(
    <MemoryRouter initialEntries={['/hired-agents?customer_id=CUST-1&agent_id=AGT-MKT-HEALTH-001&selected_hired_instance_id=HIRE-1&correlation_id=corr-1']}>
      <Routes>
        <Route path="/hired-agents" element={React.createElement(HiredAgentsOps as any) as any} />
        <Route path="/review-queue" element={<LocationEcho />} />
      </Routes>
    </MemoryRouter>
  )

  await waitFor(() => {
    expect(mocks.listOpsHiredAgents).toHaveBeenCalledWith(
      expect.objectContaining({ customer_id: 'CUST-1' })
    )
  })

  await waitFor(() => {
    expect(screen.getByText('Operator handoff context')).toBeInTheDocument()
  })

  expect(screen.getByText(/Customer CUST-1 • Agent AGT-MKT-HEALTH-001 • Runtime HIRE-1/)).toBeInTheDocument()
  expect(screen.getByDisplayValue('corr-1')).toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: 'Open Review Queue' }))

  await waitFor(() => {
    expect(screen.getByTestId('location-display')).toHaveTextContent('/review-queue?customer_id=CUST-1&agent_id=AGT-MKT-HEALTH-001&correlation_id=corr-1')
  })
})

