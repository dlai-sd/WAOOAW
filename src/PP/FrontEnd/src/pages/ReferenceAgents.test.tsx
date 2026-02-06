import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { expect, test, vi } from 'vitest'

import ReferenceAgents from './ReferenceAgents'

const mocks = vi.hoisted(() => {
  return {
    listReferenceAgents: vi.fn(async () => [
      {
        agent_id: 'AGT-MKT-CAKE-001',
        display_name: 'Cake Shop Marketing Agent',
        agent_type: 'marketing',
        spec: { version: '1.0' }
      },
      {
        agent_id: 'AGT-TRD-DELTA-001',
        display_name: 'Delta Futures Trading Agent',
        agent_type: 'trading',
        spec: { version: '1.0' }
      }
    ]),
    runReferenceAgent: vi.fn(async () => ({
      agent_id: 'AGT-MKT-CAKE-001',
      agent_type: 'marketing',
      status: 'draft',
      review: null,
      published: false,
      draft: {
        output: {
          canonical: {
            core_message: 'Hello world'
          }
        }
      }
    }))
  }
})

vi.mock('../services/gatewayApiClient', () => {
  return {
    gatewayApiClient: {
      listReferenceAgents: mocks.listReferenceAgents,
      runReferenceAgent: mocks.runReferenceAgent
    }
  }
})

test('ReferenceAgents renders list from API', async () => {
  render(<ReferenceAgents />)

  await waitFor(() => {
    expect(screen.getByText('Available Agents (2)')).toBeInTheDocument()
  })

  expect(screen.getByText('Cake Shop Marketing Agent')).toBeInTheDocument()
  expect(screen.getByText(/AGT-MKT-CAKE-001/)).toBeInTheDocument()
  expect(screen.getByText('Delta Futures Trading Agent')).toBeInTheDocument()
  expect(screen.getByText(/AGT-TRD-DELTA-001/)).toBeInTheDocument()
})

test('ReferenceAgents can run a draft and render output', async () => {
  render(<ReferenceAgents />)

  await waitFor(() => {
    expect(screen.getByText('Available Agents (2)')).toBeInTheDocument()
  })

  const runButtons = screen.getAllByRole('button', { name: 'Run Draft' })
  fireEvent.click(runButtons[0])

  await waitFor(() => {
    expect(screen.getByText('Run Result')).toBeInTheDocument()
  })

  expect(mocks.runReferenceAgent).toHaveBeenCalledTimes(1)
  expect(mocks.runReferenceAgent.mock.calls[0]?.[0]).toBe('AGT-MKT-CAKE-001')
  expect(screen.getByText(/Status: draft/i)).toBeInTheDocument()
  expect(screen.getByText(/Hello world/)).toBeInTheDocument()
})

test('ReferenceAgents trading runner sends trading fields', async () => {
  mocks.runReferenceAgent.mockResolvedValueOnce({
    agent_id: 'AGT-TRD-DELTA-001',
    agent_type: 'trading',
    status: 'draft',
    review: null,
    published: false,
    draft: { ok: true }
  })

  render(<ReferenceAgents />)

  await waitFor(() => {
    expect(screen.getByText('Delta Futures Trading Agent')).toBeInTheDocument()
  })

  fireEvent.change(screen.getAllByPlaceholderText('EXCH-...')[0], { target: { value: 'EXCH-123' } })
  fireEvent.change(screen.getAllByPlaceholderText('BTC')[0], { target: { value: 'ETH' } })
  fireEvent.change(screen.getAllByPlaceholderText('1')[0], { target: { value: '2' } })
  fireEvent.change(screen.getAllByPlaceholderText('long')[0], { target: { value: 'short' } })
  fireEvent.change(screen.getAllByPlaceholderText('enter')[0], { target: { value: 'exit' } })
  fireEvent.change(screen.getAllByPlaceholderText('place_order')[0], { target: { value: 'close_position' } })
  fireEvent.change(screen.getAllByPlaceholderText('APR-...')[0], { target: { value: 'APR-777' } })

  const runButtons = screen.getAllByRole('button', { name: 'Run Draft' })
  fireEvent.click(runButtons[1])

  await waitFor(() => {
    expect(mocks.runReferenceAgent).toHaveBeenCalled()
  })

  const lastCall = mocks.runReferenceAgent.mock.calls[mocks.runReferenceAgent.mock.calls.length - 1]
  expect(lastCall?.[0]).toBe('AGT-TRD-DELTA-001')

  const payload = lastCall?.[1] as any
  expect(payload.exchange_account_id).toBe('EXCH-123')
  expect(payload.coin).toBe('ETH')
  expect(payload.units).toBe(2)
  expect(payload.side).toBe('short')
  expect(payload.action).toBe('exit')
  expect(payload.intent_action).toBe('close_position')
  expect(payload.approval_id).toBe('APR-777')
})
