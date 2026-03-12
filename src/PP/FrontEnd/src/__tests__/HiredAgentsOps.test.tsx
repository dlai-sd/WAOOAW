import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { expect, test, vi } from 'vitest'

const mockGatewayApiClient = vi.hoisted(() => ({
  listOpsSubscriptions: vi.fn(async () => []),
  listReferenceAgents: vi.fn(async () => [{ agent_id: 'AGT-MKT-DMA-001', display_name: 'Digital Marketing Agent' }]),
  listOpsHiredAgents: vi.fn(async () => []),
  lookupCustomerByEmail: vi.fn(),
  getCustomerById: vi.fn(async () => ({ customer_id: 'CUST-9', email: 'owner@example.com' })),
  getOpsHiredAgent: vi.fn(async () => ({})),
  listOpsHiredAgentGoals: vi.fn(async () => ({ goals: [] })),
  listOpsHiredAgentDeliverables: vi.fn(async () => ({ deliverables: [] })),
  listApprovals: vi.fn(async () => ({ approvals: [] })),
  listPolicyDenials: vi.fn(async () => ({ records: [] })),
  listOpsHiredAgentSkills: vi.fn(async () => ([])),
  listOpsPlatformConnections: vi.fn(async () => ([])),
}))

vi.mock('../services/gatewayApiClient', () => ({
  gatewayApiClient: mockGatewayApiClient,
}))

vi.mock('../components/ApiErrorPanel', () => ({
  default: ({ title }: { title: string }) => <div>{title}</div>,
}))
vi.mock('../components/ConstructHealthPanel', () => ({
  default: () => <div>ConstructHealthPanel</div>,
}))
vi.mock('../components/SchedulerDiagnosticsPanel', () => ({
  default: () => <div>SchedulerDiagnosticsPanel</div>,
}))
vi.mock('../components/HookTracePanel', () => ({
  default: () => <div>HookTracePanel</div>,
}))

import HiredAgentsOps from '../pages/HiredAgentsOps'

test('E9-S1-T1: Lookup button populates Customer ID when email resolves', async () => {
  mockGatewayApiClient.lookupCustomerByEmail.mockResolvedValueOnce({ customer_id: 'C1', email: 'test@example.com' })
  const user = userEvent.setup()

  render(
    <MemoryRouter initialEntries={['/hired-agents']}>
      <Routes>
        <Route path="/hired-agents" element={<HiredAgentsOps />} />
      </Routes>
    </MemoryRouter>
  )

  const emailInput = screen.getByRole('textbox', { name: /customer email/i })
  await user.type(emailInput, 'test@example.com')
  await user.click(screen.getByRole('button', { name: /lookup/i }))

  await waitFor(() => {
    const customerIdInput = screen.getByRole('textbox', { name: /customer id/i })
    expect(customerIdInput).toHaveValue('C1')
  })
})

test('E9-S1-T2: Lookup button shows error message when email not found', async () => {
  mockGatewayApiClient.lookupCustomerByEmail.mockRejectedValueOnce(new Error('Not found'))
  const user = userEvent.setup()

  render(
    <MemoryRouter initialEntries={['/hired-agents']}>
      <Routes>
        <Route path="/hired-agents" element={<HiredAgentsOps />} />
      </Routes>
    </MemoryRouter>
  )

  const emailInput = screen.getByRole('textbox', { name: /customer email/i })
  await user.type(emailInput, 'notfound@example.com')
  await user.click(screen.getByRole('button', { name: /lookup/i }))

  await waitFor(() => {
    expect(screen.getByText('Customer not found for this email address.')).toBeInTheDocument()
  })
})

test('I3-S1-T1: Hired agent ops shows digital marketing brief and truthful publish state', async () => {
  mockGatewayApiClient.listOpsSubscriptions.mockResolvedValueOnce([
    { subscription_id: 'SUB-1', agent_id: 'AGT-MKT-DMA-001', status: 'active', duration: 'monthly' }
  ])
  mockGatewayApiClient.listOpsHiredAgents.mockResolvedValueOnce([
    {
      hired_instance_id: 'HIRE-1',
      subscription_id: 'SUB-1',
      agent_id: 'AGT-MKT-DMA-001',
      agent_type_id: 'marketing.digital_marketing.v1',
      configured: true,
      goals_completed: true,
      trial_status: 'active',
      config: { timezone: 'Asia/Kolkata' }
    }
  ])
  mockGatewayApiClient.listOpsHiredAgentGoals.mockResolvedValueOnce({ hired_instance_id: 'HIRE-1', goals: [] })
  mockGatewayApiClient.listOpsHiredAgentDeliverables.mockResolvedValueOnce({
    hired_instance_id: 'HIRE-1',
    deliverables: [
      {
        deliverable_id: 'DEL-1',
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
  mockGatewayApiClient.listApprovals.mockResolvedValueOnce({ approvals: [] })
  mockGatewayApiClient.listPolicyDenials.mockResolvedValueOnce({ records: [] })
  mockGatewayApiClient.listOpsHiredAgentSkills.mockResolvedValueOnce([
    {
      skill_id: 'skill-theme-discovery',
      display_name: 'Theme Discovery',
      goal_schema: {
        fields: [
          { key: 'business_name', label: 'Business name', required: true },
          { key: 'audience', label: 'Audience', required: true }
        ]
      },
      goal_config: {
        business_name: 'WAOOAW Studio',
        audience: 'Founders launching YouTube content'
      }
    }
  ])
  mockGatewayApiClient.listOpsPlatformConnections.mockResolvedValueOnce([])

  const user = userEvent.setup()

  render(
    <MemoryRouter initialEntries={['/hired-agents']}>
      <Routes>
        <Route path="/hired-agents" element={<HiredAgentsOps />} />
      </Routes>
    </MemoryRouter>
  )

  await user.type(screen.getByRole('textbox', { name: /customer id/i }), 'CUST-9')
  await user.click(screen.getByRole('button', { name: 'Load' }))

  await waitFor(() => {
    expect(screen.getByText('HIRE-1')).toBeInTheDocument()
  })

  await waitFor(() => {
    expect(mockGatewayApiClient.getCustomerById).toHaveBeenCalledWith('CUST-9')
  })

  expect(screen.getByText('Digital Marketing Agent')).toBeInTheDocument()

  await user.click(screen.getByText('HIRE-1'))

  await waitFor(() => {
    expect(screen.getByTestId('pp-dma-brief-summary-card')).toBeInTheDocument()
  })

  expect(screen.getByText('WAOOAW Studio')).toBeInTheDocument()
  expect(screen.getByText(/owner@example.com • Digital Marketing Agent • Runtime HIRE-1/)).toBeInTheDocument()
  expect(screen.getByTestId('pp-dma-publish-readiness')).toHaveTextContent('Blocked by channel connection')
  expect(screen.getByTestId('pp-dma-channel-status')).toHaveTextContent('Youtube not connected')
  expect(screen.getByTestId('pp-dma-block-owner')).toHaveTextContent('Platform action required')
})
