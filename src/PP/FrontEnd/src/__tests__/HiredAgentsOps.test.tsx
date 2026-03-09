import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, test, vi } from 'vitest'

// Mock gatewayApiClient
const mockGatewayApiClient = {
  listOpsSubscriptions: vi.fn(async () => []),
  listOpsHiredAgents: vi.fn(async () => []),
  lookupCustomerByEmail: vi.fn(),
  getOpsHiredAgent: vi.fn(async () => ({})),
  listOpsHiredAgentGoals: vi.fn(async () => ({ goals: [] })),
  listOpsHiredAgentDeliverables: vi.fn(async () => ({ deliverables: [] })),
  listOpsApprovals: vi.fn(async () => ({ approvals: [] })),
  listOpsPolicyDenials: vi.fn(async () => ({ records: [] })),
}

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

  render(<HiredAgentsOps />)

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

  render(<HiredAgentsOps />)

  const emailInput = screen.getByRole('textbox', { name: /customer email/i })
  await user.type(emailInput, 'notfound@example.com')
  await user.click(screen.getByRole('button', { name: /lookup/i }))

  await waitFor(() => {
    expect(screen.getByText('Customer not found for this email address.')).toBeInTheDocument()
  })
})
