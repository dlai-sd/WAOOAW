import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, test, vi } from 'vitest'

import ConstructHealthPanel from '../components/ConstructHealthPanel'

const mockHealthData = {
  hired_agent_id: 'HIRE-1',
  scheduler: { status: 'healthy', next_run: '2026-03-08T09:00:00Z' },
  pump: { status: 'degraded', lag_seconds: 7200 },
  processor: { status: 'healthy', tasks_today: 5 },
  connector: { status: 'healthy', secret_ref: 'abcxyz1234' },
  publisher: { status: 'offline' },
  policy: { status: 'healthy', approval_mode: 'manual' },
}

const mocks = vi.hoisted(() => ({
  gatewayRequestJson: vi.fn(async () => mockHealthData),
}))

vi.mock('../services/gatewayApiClient', () => ({
  gatewayRequestJson: mocks.gatewayRequestJson,
  GatewayApiError: class GatewayApiError extends Error {},
}))

test('ConstructHealthPanel renders 6 construct cards', async () => {
  render(
    <ConstructHealthPanel
      hiredAgentId="HIRE-1"
      isOpen={true}
      onClose={() => {}}
    />
  )

  await waitFor(() => {
    expect(screen.getByText('Scheduler')).toBeInTheDocument()
  })

  expect(screen.getByText('Pump')).toBeInTheDocument()
  expect(screen.getByText('Processor')).toBeInTheDocument()
  expect(screen.getByText('Connector')).toBeInTheDocument()
  expect(screen.getByText('Publisher')).toBeInTheDocument()
  expect(screen.getByText('Policy')).toBeInTheDocument()
})

test('ConstructHealthPanel shows status dots with correct aria-labels', async () => {
  render(
    <ConstructHealthPanel
      hiredAgentId="HIRE-1"
      isOpen={true}
      onClose={() => {}}
    />
  )

  await waitFor(() => {
    expect(screen.getAllByLabelText('status: healthy').length).toBeGreaterThan(0)
  })

  expect(screen.getAllByLabelText('status: degraded').length).toBeGreaterThan(0)
  expect(screen.getAllByLabelText('status: offline').length).toBeGreaterThan(0)
})

test('ConstructHealthPanel masks connector secret_ref as ****{last4}', async () => {
  render(
    <ConstructHealthPanel
      hiredAgentId="HIRE-1"
      isOpen={true}
      onClose={() => {}}
    />
  )

  await waitFor(() => {
    expect(screen.getByText('secret_ref: ****1234')).toBeInTheDocument()
  })
})

test('ConstructHealthPanel calls onClose when close button is clicked', async () => {
  const user = userEvent.setup()
  const onClose = vi.fn()

  render(
    <ConstructHealthPanel
      hiredAgentId="HIRE-1"
      isOpen={true}
      onClose={onClose}
    />
  )

  await waitFor(() => {
    expect(screen.getByText('Construct Health')).toBeInTheDocument()
  })

  await user.click(screen.getByRole('button', { name: '✕' }))
  expect(onClose).toHaveBeenCalledOnce()
})

test('ConstructHealthPanel does not render when isOpen=false', () => {
  render(
    <ConstructHealthPanel
      hiredAgentId="HIRE-1"
      isOpen={false}
      onClose={() => {}}
    />
  )

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
})

test('useConstructHealth returns isLoading=true while fetching', async () => {
  let resolvePromise!: (value: unknown) => void
  mocks.gatewayRequestJson.mockImplementationOnce(
    () => new Promise((res) => { resolvePromise = res })
  )

  render(
    <ConstructHealthPanel
      hiredAgentId="HIRE-1"
      isOpen={true}
      onClose={() => {}}
    />
  )

  await waitFor(() => {
    expect(screen.getByText('Loading construct health...')).toBeInTheDocument()
  })

  resolvePromise(mockHealthData)
  await waitFor(() => {
    expect(screen.queryByText('Loading construct health...')).not.toBeInTheDocument()
  })
})
