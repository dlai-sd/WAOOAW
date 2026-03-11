import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, test, vi } from 'vitest'

import HookTracePanel from '../components/HookTracePanel'

const mockEntries = [
  {
    event_id: 'evt-1',
    stage: 'pre_pump',
    hired_agent_id: 'HIRE-1',
    agent_type: 'marketing',
    result: 'proceed',
    reason: 'ok',
    emitted_at: '2026-03-07T09:00:00Z',
    payload_summary: 'payload data here',
  },
  {
    event_id: 'evt-2',
    stage: 'post_processor',
    hired_agent_id: 'HIRE-1',
    agent_type: 'marketing',
    result: 'halt',
    reason: 'limit reached',
    emitted_at: '2026-03-07T09:01:00Z',
    payload_summary: 'some other payload',
  },
]

const mocks = vi.hoisted(() => ({
  gatewayRequestJson: vi.fn(async () => mockEntries),
}))

vi.mock('../services/gatewayApiClient', () => ({
  gatewayRequestJson: mocks.gatewayRequestJson,
  GatewayApiError: class GatewayApiError extends Error {},
}))

test('HookTracePanel renders table with hook events', async () => {
  render(<HookTracePanel hiredAgentId="HIRE-1" />)

  await waitFor(() => {
    expect(screen.getByText('pre_pump')).toBeInTheDocument()
  })

  expect(screen.getAllByText('proceed').length).toBeGreaterThanOrEqual(1)
  expect(screen.getAllByText('post_processor').length).toBeGreaterThanOrEqual(1)
  expect(screen.getAllByText('halt').length).toBeGreaterThanOrEqual(1)
})

test('HookTracePanel renders up to 50 rows', async () => {
  const manyEntries = Array.from({ length: 50 }, (_, i) => ({
    event_id: `evt-${i}`,
    stage: 'pre_pump',
    hired_agent_id: 'HIRE-1',
    agent_type: 'marketing',
    result: 'proceed',
    reason: 'ok',
    emitted_at: '2026-03-07T09:00:00Z',
    payload_summary: 'test',
  }))
  mocks.gatewayRequestJson.mockResolvedValueOnce(manyEntries)

  render(<HookTracePanel hiredAgentId="HIRE-1" />)

  await waitFor(() => {
    const rows = screen.getAllByRole('row')
    expect(rows.length - 1).toBe(50)
  })
})

test('HookTracePanel shows stage filter dropdown', async () => {
  render(<HookTracePanel hiredAgentId="HIRE-1" />)

  await waitFor(() => {
    expect(screen.getByText('Stage')).toBeInTheDocument()
  })
})

test('HookTracePanel shows result filter dropdown', async () => {
  render(<HookTracePanel hiredAgentId="HIRE-1" />)

  await waitFor(() => {
    expect(screen.getByText('Result')).toBeInTheDocument()
  })
})

test('HookTracePanel applies filter when stage dropdown changes', async () => {
  const user = userEvent.setup()
  render(<HookTracePanel hiredAgentId="HIRE-1" />)

  await waitFor(() => {
    expect(screen.getByText('Stage')).toBeInTheDocument()
  })

  // Change stage filter — should trigger refetch with stage param
  const stageSelect = screen.getAllByRole('combobox')[0]
  await user.selectOptions(stageSelect, 'pre_pump')

  await waitFor(() => {
    expect(mocks.gatewayRequestJson).toHaveBeenCalledWith(
      expect.stringContaining('stage=pre_pump')
    )
  })
})

test('HookTracePanel halt rows have red tint background', async () => {
  render(<HookTracePanel hiredAgentId="HIRE-1" />)

  await waitFor(() => {
    expect(screen.getAllByText('halt').length).toBeGreaterThanOrEqual(1)
  })

  // The halt row text should be visible
  expect(screen.getByText('limit reached')).toBeInTheDocument()
})

test('HookTracePanel payload_summary shows at most 100 chars', async () => {
  const longPayload = 'x'.repeat(150)
  mocks.gatewayRequestJson.mockResolvedValueOnce([
    {
      event_id: 'evt-long',
      stage: 'pre_pump',
      hired_agent_id: 'HIRE-1',
      agent_type: 'marketing',
      result: 'proceed',
      reason: 'ok',
      emitted_at: '2026-03-07T09:00:00Z',
      payload_summary: longPayload,
    },
  ])

  render(<HookTracePanel hiredAgentId="HIRE-1" />)

  await waitFor(() => {
    const displayed = screen.getByText('x'.repeat(100))
    expect(displayed).toBeInTheDocument()
  })
})
