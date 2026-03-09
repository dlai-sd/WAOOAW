import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { expect, test, vi } from 'vitest'
import type { ReactNode } from 'react'

vi.mock('react-router-dom', () => ({
  Link: ({ children, to }: { children: ReactNode; to: string }) => (
    <a href={to}>{children}</a>
  ),
}))

const mockGatewayApiClient = {
  listAgents: vi.fn(async () => []),
  listAgentTypeDefinitions: vi.fn(async () => []),
  getAgentTypeDefinition: vi.fn(),
  publishAgentTypeDefinition: vi.fn(),
}

vi.mock('../services/gatewayApiClient', () => ({
  gatewayApiClient: mockGatewayApiClient,
}))

vi.mock('../components/ApiErrorPanel', () => ({
  default: ({ title }: { title: string }) => <div>{title}</div>,
}))

import AgentManagement from '../pages/AgentManagement'

test('E11-S1-T1: AgentManagement renders without error and has no "AGT-" text in DOM', async () => {
  render(<AgentManagement />)

  await waitFor(() => {
    expect(screen.getByText('Agent Management')).toBeInTheDocument()
  })

  // DEF-015 audit: no hardcoded AGT-* IDs in rendered output
  expect(screen.queryByText(/AGT-/)).not.toBeInTheDocument()
})
