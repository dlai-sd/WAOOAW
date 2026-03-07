import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, test, vi } from 'vitest'

import ConstraintPolicyLiveTuneDrawer from '../components/ConstraintPolicyLiveTuneDrawer'

const mockPolicy = {
  approval_mode: 'manual',
  max_tasks_per_day: 10,
  max_position_size_inr: 0,
  trial_task_limit: 10,
}

const mocks = vi.hoisted(() => ({
  gatewayRequestJson: vi.fn(async () => ({
    agent_setup_id: 'setup-1',
    constraint_policy: { approval_mode: 'auto', max_tasks_per_day: 5 },
  })),
}))

vi.mock('../services/gatewayApiClient', () => ({
  gatewayRequestJson: mocks.gatewayRequestJson,
  GatewayApiError: class GatewayApiError extends Error {},
}))

test('ConstraintPolicyLiveTuneDrawer renders approval_mode toggle and max_tasks_per_day input', () => {
  render(
    <ConstraintPolicyLiveTuneDrawer
      agentSetupId="setup-1"
      currentPolicy={mockPolicy}
      isOpen={true}
      onClose={() => {}}
      onSuccess={() => {}}
    />
  )

  expect(screen.getByRole('button', { name: 'Set manual approval mode' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Set auto approval mode' })).toBeInTheDocument()
  expect(screen.getByLabelText(/max tasks per day/i)).toBeInTheDocument()
})

test('ConstraintPolicyLiveTuneDrawer submit button is disabled until audit checkbox is checked', async () => {
  const user = userEvent.setup()
  render(
    <ConstraintPolicyLiveTuneDrawer
      agentSetupId="setup-1"
      currentPolicy={mockPolicy}
      isOpen={true}
      onClose={() => {}}
      onSuccess={() => {}}
    />
  )

  const submitBtn = screen.getByRole('button', { name: 'Apply Policy Change' })
  expect(submitBtn).toBeDisabled()

  const checkbox = screen.getByRole('checkbox')
  await user.click(checkbox)

  await waitFor(() => {
    expect(submitBtn).not.toBeDisabled()
  })
})

test('ConstraintPolicyLiveTuneDrawer calls PATCH endpoint and onSuccess on submit', async () => {
  const user = userEvent.setup()
  const onSuccess = vi.fn()
  const onClose = vi.fn()

  render(
    <ConstraintPolicyLiveTuneDrawer
      agentSetupId="setup-1"
      currentPolicy={mockPolicy}
      isOpen={true}
      onClose={onClose}
      onSuccess={onSuccess}
    />
  )

  const checkbox = screen.getByRole('checkbox')
  await user.click(checkbox)

  const submitBtn = screen.getByRole('button', { name: 'Apply Policy Change' })
  await user.click(submitBtn)

  await waitFor(() => {
    expect(mocks.gatewayRequestJson).toHaveBeenCalledWith(
      expect.stringContaining('/pp/agent-setups/setup-1/constraint-policy'),
      expect.objectContaining({ method: 'PATCH' })
    )
    expect(onSuccess).toHaveBeenCalledOnce()
    expect(onClose).toHaveBeenCalledOnce()
  })
})

test('ConstraintPolicyLiveTuneDrawer does not render when isOpen=false', () => {
  render(
    <ConstraintPolicyLiveTuneDrawer
      agentSetupId="setup-1"
      currentPolicy={mockPolicy}
      isOpen={false}
      onClose={() => {}}
      onSuccess={() => {}}
    />
  )

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
})

test('ConstraintPolicyLiveTuneDrawer calls onClose when close button is clicked', async () => {
  const user = userEvent.setup()
  const onClose = vi.fn()

  render(
    <ConstraintPolicyLiveTuneDrawer
      agentSetupId="setup-1"
      currentPolicy={mockPolicy}
      isOpen={true}
      onClose={onClose}
      onSuccess={() => {}}
    />
  )

  await user.click(screen.getByRole('button', { name: 'Close' }))
  expect(onClose).toHaveBeenCalledOnce()
})
