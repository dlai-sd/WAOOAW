import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, test, vi } from 'vitest'

import AgentTypeSetupScreen from '../pages/AgentTypeSetupScreen'

const mocks = vi.hoisted(() => ({
  gatewayRequestJson: vi.fn(async () => []),
}))

vi.mock('../services/gatewayApiClient', () => ({
  gatewayRequestJson: mocks.gatewayRequestJson,
  GatewayApiError: class GatewayApiError extends Error {},
}))

test('AgentTypeSetupScreen renders all 4 form sections', async () => {
  render(<AgentTypeSetupScreen />)

  expect(screen.getByText('1. Identity')).toBeInTheDocument()
  expect(screen.getByText('2. Construct Bindings')).toBeInTheDocument()
  expect(screen.getByText('3. Constraint Policy')).toBeInTheDocument()
  expect(screen.getByText('4. Hook Checklist')).toBeInTheDocument()
})

test('AgentTypeSetupScreen renders approval_mode toggle with Manual and Auto labels', () => {
  render(<AgentTypeSetupScreen />)

  expect(screen.getByRole('button', { name: 'Manual approval mode' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Auto approval mode' })).toBeInTheDocument()
})

test('AgentTypeSetupScreen hides max_position_size_inr when connector_class is not trading', () => {
  render(<AgentTypeSetupScreen />)

  expect(screen.queryByLabelText(/max position size/i)).not.toBeInTheDocument()
})

test('AgentTypeSetupScreen shows max_position_size_inr when connector_class includes trading', async () => {
  const user = userEvent.setup()
  render(<AgentTypeSetupScreen />)

  // connector_class and publisher_class both have placeholder "None"
  // connector_class input is the first one (index 0)
  const noneInputs = screen.getAllByPlaceholderText('None')
  const connectorInput = noneInputs[0]
  await user.clear(connectorInput)
  await user.type(connectorInput, 'TradingConnector')

  await waitFor(() => {
    expect(screen.getByLabelText(/max position size/i)).toBeInTheDocument()
  })
})

test('AgentTypeSetupScreen AuditHook checkbox is disabled and checked', () => {
  render(<AgentTypeSetupScreen />)

  const auditHookCheckbox = screen.getByRole('checkbox', { name: /audit hook/i })
  expect(auditHookCheckbox).toBeChecked()
  expect(auditHookCheckbox).toBeDisabled()
})

test('AgentTypeSetupScreen shows validation errors when required fields are empty', async () => {
  const user = userEvent.setup()
  render(<AgentTypeSetupScreen />)

  await user.click(screen.getByRole('button', { name: 'Create' }))

  await waitFor(() => {
    expect(screen.getByText('Agent type is required')).toBeInTheDocument()
  })
  expect(screen.getByText('Display name is required')).toBeInTheDocument()
})

test('AgentTypeSetupScreen calls loadClassOptions on mount', async () => {
  mocks.gatewayRequestJson.mockImplementation(async (path: string) => {
    if (String(path).includes('processors') || String(path).includes('pumps')) return []
    return {}
  })

  render(<AgentTypeSetupScreen />)

  await waitFor(() => {
    // loadClassOptions is called on mount — it calls gatewayRequestJson for processors and pumps
    expect(mocks.gatewayRequestJson).toHaveBeenCalled()
  })
})

test('AgentTypeSetupScreen renders with edit mode title when agentSetupId is provided', () => {
  render(<AgentTypeSetupScreen agentSetupId="setup-123" />)

  expect(screen.getByText('Edit Agent Type Setup')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Update' })).toBeInTheDocument()
})
