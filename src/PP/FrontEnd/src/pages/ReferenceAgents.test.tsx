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
    expect(screen.getByText('Available Agents (1)')).toBeInTheDocument()
  })

  expect(screen.getByText('Cake Shop Marketing Agent')).toBeInTheDocument()
  expect(screen.getByText(/AGT-MKT-CAKE-001/)).toBeInTheDocument()
})

test('ReferenceAgents can run a draft and render output', async () => {
  render(<ReferenceAgents />)

  await waitFor(() => {
    expect(screen.getByText('Available Agents (1)')).toBeInTheDocument()
  })

  const runButton = screen.getByRole('button', { name: 'Run Draft' })
  fireEvent.click(runButton)

  await waitFor(() => {
    expect(screen.getByText('Run Result')).toBeInTheDocument()
  })

  expect(mocks.runReferenceAgent).toHaveBeenCalledTimes(1)
  expect(mocks.runReferenceAgent.mock.calls[0]?.[0]).toBe('AGT-MKT-CAKE-001')
  expect(screen.getByText(/Status: draft/i)).toBeInTheDocument()
  expect(screen.getByText(/Hello world/)).toBeInTheDocument()
})
