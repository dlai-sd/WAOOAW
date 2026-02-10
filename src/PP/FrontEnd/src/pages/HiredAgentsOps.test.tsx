import '@testing-library/jest-dom/vitest'
import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, test, vi } from 'vitest'

import HiredAgentsOps from './HiredAgentsOps'

const mocks = vi.hoisted(() => {
  return {
    listSubscriptionsByCustomer: vi.fn(async () => [
      { subscription_id: 'SUB-1', agent_id: 'AGT-MKT-HEALTH-001', status: 'active', duration: 'monthly' }
    ]),
    getHiredAgentBySubscription: vi.fn(async () => ({
      hired_instance_id: 'HIRE-1',
      subscription_id: 'SUB-1',
      agent_id: 'AGT-MKT-HEALTH-001',
      configured: true,
      goals_completed: true,
      trial_status: 'active',
      config: { timezone: 'Asia/Kolkata' }
    })),
    listGoalsForHiredInstance: vi.fn(async () => ({
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
    listDeliverablesForHiredInstance: vi.fn(async () => ({
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
        listSubscriptionsByCustomer: mocks.listSubscriptionsByCustomer,
        getHiredAgentBySubscription: mocks.getHiredAgentBySubscription,
        listGoalsForHiredInstance: mocks.listGoalsForHiredInstance,
        listDeliverablesForHiredInstance: mocks.listDeliverablesForHiredInstance,
        listApprovals: mocks.listApprovals,
        listPolicyDenials: mocks.listPolicyDenials
      }
    }
  })
})

test('HiredAgentsOps loads instances and renders drilldown sections', async () => {
  const user = userEvent.setup()
  render(React.createElement(HiredAgentsOps as any) as any)

  await waitFor(() => {
    expect(screen.getByText('Hired Agents')).toBeInTheDocument()
  })

  await user.type(screen.getByLabelText('Customer ID'), 'CUST-1')
  await user.click(screen.getByRole('button', { name: 'Load' }))

  await waitFor(() => {
    expect(mocks.listSubscriptionsByCustomer).toHaveBeenCalledWith('CUST-1')
  })

  await waitFor(() => {
    expect(screen.getByText('HIRE-1')).toBeInTheDocument()
  })

  await user.click(screen.getByText('HIRE-1'))

  await waitFor(() => {
    expect(mocks.listDeliverablesForHiredInstance).toHaveBeenCalledTimes(1)
    expect(mocks.listApprovals).toHaveBeenCalledTimes(1)
    expect(mocks.listPolicyDenials).toHaveBeenCalledTimes(1)
  })

  expect(screen.getByText('Drafts (Deliverables)')).toBeInTheDocument()
  expect(screen.getByText('DEL-1')).toBeInTheDocument()
  expect(screen.getByText('Approvals')).toBeInTheDocument()
  expect(screen.getByText('APR-1')).toBeInTheDocument()
  expect(screen.getByText('Policy Denials')).toBeInTheDocument()
  expect(screen.getByText('approval_required')).toBeInTheDocument()
})
