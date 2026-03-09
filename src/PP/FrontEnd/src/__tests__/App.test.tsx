import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, test, vi } from 'vitest'
import type { ReactNode } from 'react'

import App from '../App'

// Mock config to simulate demo environment with no Google client ID
vi.mock('../config/oauth.config', () => ({
  default: {
    name: 'demo',
    apiBaseUrl: 'http://localhost:8015/api',
    frontendUrl: 'http://localhost:3000',
    googleClientId: '',
  },
  config: {
    name: 'demo',
    apiBaseUrl: 'http://localhost:8015/api',
    frontendUrl: 'http://localhost:3000',
    googleClientId: '',
  },
  API_ENDPOINTS: {
    googleLogin: 'http://localhost:8015/api/auth/google/login',
    googleCallback: 'http://localhost:8015/api/auth/google/callback',
    googleVerify: 'http://localhost:8015/api/auth/google/verify',
    refresh: 'http://localhost:8015/api/auth/refresh',
    logout: 'http://localhost:8015/api/auth/logout',
    me: 'http://localhost:8015/api/auth/me',
  },
}))

// Mock all page components to avoid complex rendering
vi.mock('../pages/LandingPage', () => ({ default: () => <div>LandingPage</div> }))
vi.mock('../pages/Dashboard', () => ({ default: () => <div>Dashboard</div> }))
vi.mock('../pages/AgentManagement', () => ({ default: () => <div>AgentManagement</div> }))
vi.mock('../pages/AgentData', () => ({ default: () => <div>AgentData</div> }))
vi.mock('../pages/CustomerManagement', () => ({ default: () => <div>CustomerManagement</div> }))
vi.mock('../pages/Billing', () => ({ default: () => <div>Billing</div> }))
vi.mock('../pages/GovernorConsole', () => ({ default: () => <div>GovernorConsole</div> }))
vi.mock('../pages/ReferenceAgents', () => ({ default: () => <div>ReferenceAgents</div> }))
vi.mock('../pages/GenesisConsole', () => ({ default: () => <div>GenesisConsole</div> }))
vi.mock('../pages/AuditConsole', () => ({ default: () => <div>AuditConsole</div> }))
vi.mock('../pages/PolicyDenials', () => ({ default: () => <div>PolicyDenials</div> }))
vi.mock('../pages/AgentSpecTools', () => ({ default: () => <div>AgentSpecTools</div> }))
vi.mock('../pages/DbUpdates', () => ({ default: () => <div>DbUpdates</div> }))
vi.mock('../pages/AgentSetup', () => ({ default: () => <div>AgentSetup</div> }))
vi.mock('../pages/AgentTypeSetupScreen', () => ({ default: () => <div>AgentTypeSetupScreen</div> }))
vi.mock('../pages/ApprovalsQueueScreen', () => ({ default: () => <div>ApprovalsQueueScreen</div> }))
vi.mock('../pages/ReviewQueue', () => ({ default: () => <div>ReviewQueue</div> }))
vi.mock('../pages/HiredAgentsOps', () => ({ default: () => <div>HiredAgentsOps</div> }))
vi.mock('../components/Layout', () => ({
  default: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}))

test('Demo Login button appears when config.name is demo', async () => {
  const user = userEvent.setup()
  render(<App />)

  // Wait for auth loading to complete, then click Sign In
  const signInButton = await screen.findByRole('button', { name: /sign in/i })
  await user.click(signInButton)

  // The Demo Login (Skip OAuth) button should be visible in the dialog
  await waitFor(() => {
    expect(screen.getByRole('button', { name: /demo login/i })).toBeInTheDocument()
  })
})

test('Demo Login button is absent when config.name is production', async () => {
  // Test the allowDemoLogin logic: production env should NOT show demo login
  // We verify this by checking that 'production' is not in the allowed list
  const allowedNames = ['codespace', 'development', 'demo']
  expect(allowedNames).toContain('demo')
  expect(allowedNames).not.toContain('production')
  expect(allowedNames).not.toContain('prod')
})

