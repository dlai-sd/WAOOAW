import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { expect, test, vi } from 'vitest'

import SchedulerDiagnosticsPanel, { describeCron } from '../components/SchedulerDiagnosticsPanel'

const mockDiagnostics = {
  hired_agent_id: 'HIRE-1',
  cron_expression: '0 9 * * 1-5',
  next_run: '2026-03-09T09:00:00Z',
  last_run: '2026-03-07T09:00:00Z',
  lag_seconds: 120,
  dlq_depth: 0,
  dlq_entries: [],
  tasks_used_today: 3,
  trial_task_limit: 10,
  is_paused: false,
}

const mocks = vi.hoisted(() => ({
  gatewayRequestJson: vi.fn(async () => mockDiagnostics),
}))

vi.mock('../services/gatewayApiClient', () => ({
  gatewayRequestJson: mocks.gatewayRequestJson,
  GatewayApiError: class GatewayApiError extends Error {},
}))

test('describeCron: weekday at 9 AM', () => {
  expect(describeCron('0 9 * * 1-5')).toBe('Every weekday at 9:00')
})

test('describeCron: daily at noon', () => {
  expect(describeCron('0 12 * * *')).toBe('Daily at 12:00')
})

test('describeCron: complex expression returns Custom:', () => {
  expect(describeCron('*/15 * * * *')).toMatch(/^Custom:/)
})

test('SchedulerDiagnosticsPanel displays cron expression and description', async () => {
  render(
    <SchedulerDiagnosticsPanel hiredAgentId="HIRE-1" isAdmin={false} />
  )

  await waitFor(() => {
    expect(screen.getByText('0 9 * * 1-5')).toBeInTheDocument()
  })

  expect(screen.getByText('Every weekday at 9:00')).toBeInTheDocument()
})

test('SchedulerDiagnosticsPanel renders lag gauge', async () => {
  render(
    <SchedulerDiagnosticsPanel hiredAgentId="HIRE-1" isAdmin={false} />
  )

  await waitFor(() => {
    expect(screen.getByLabelText(/lag gauge/)).toBeInTheDocument()
  })

  expect(screen.getByText(/120s/)).toBeInTheDocument()
})

test('SchedulerDiagnosticsPanel hides DLQ section when dlq_depth=0', async () => {
  render(
    <SchedulerDiagnosticsPanel hiredAgentId="HIRE-1" isAdmin={false} />
  )

  await waitFor(() => {
    expect(screen.queryByText(/DLQ/)).not.toBeInTheDocument()
  })
})

test('SchedulerDiagnosticsPanel shows DLQ section when dlq_depth > 0', async () => {
  mocks.gatewayRequestJson.mockResolvedValueOnce({
    ...mockDiagnostics,
    dlq_depth: 2,
    dlq_entries: [
      {
        dlq_id: 'dlq-1',
        hired_agent_id: 'HIRE-1',
        failed_at: '2026-03-07T08:00:00Z',
        hook_stage: 'pre_pump',
        error_message: 'timeout',
        retry_count: 3,
      },
    ],
  })

  render(
    <SchedulerDiagnosticsPanel hiredAgentId="HIRE-1" isAdmin={false} />
  )

  await waitFor(() => {
    expect(screen.getByText(/DLQ \(2 entries\)/)).toBeInTheDocument()
  })

  expect(screen.getByText('pre_pump')).toBeInTheDocument()
  expect(screen.getByText('timeout')).toBeInTheDocument()
})

test('SchedulerDiagnosticsPanel hides Pause/Resume when isAdmin=false', async () => {
  render(
    <SchedulerDiagnosticsPanel hiredAgentId="HIRE-1" isAdmin={false} />
  )

  await waitFor(() => {
    expect(screen.getByText('0 9 * * 1-5')).toBeInTheDocument()
  })

  expect(screen.queryByRole('button', { name: 'Pause' })).not.toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Resume' })).not.toBeInTheDocument()
})

test('SchedulerDiagnosticsPanel shows Pause/Resume when isAdmin=true', async () => {
  render(
    <SchedulerDiagnosticsPanel hiredAgentId="HIRE-1" isAdmin={true} />
  )

  await waitFor(() => {
    expect(screen.getByRole('button', { name: 'Pause' })).toBeInTheDocument()
  })

  expect(screen.getByRole('button', { name: 'Resume' })).toBeInTheDocument()
})
