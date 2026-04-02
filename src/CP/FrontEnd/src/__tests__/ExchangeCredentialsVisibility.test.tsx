import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'

import { ConfigureAgentPanel } from '../pages/authenticated/MyAgents'

vi.mock('../services/hiredAgents.service', () => ({
  getHiredAgentBySubscription: vi.fn(async () => ({
    hired_instance_id: 'hire_1',
    subscription_id: 'sub_1',
    agent_id: 'AGENT-1',
    agent_type_id: 'marketing.digital_marketing.v1',
    nickname: 'Agent',
    theme: 'default',
    config: {},
    configured: true,
    goals_completed: false,
  })),
  upsertHiredAgentDraft: vi.fn(async () => ({
    hired_instance_id: 'hire_1',
    subscription_id: 'sub_1',
    agent_id: 'AGENT-1',
    agent_type_id: 'marketing.digital_marketing.v1',
    nickname: 'Agent',
    theme: 'default',
    config: {},
    configured: true,
    goals_completed: false,
  })),
}))

vi.mock('../services/agentTypes.service', () => ({
  getAgentTypeDefinition: vi.fn(async () => ({
    config_schema: {
      fields: [
        { key: 'exchange_credential_ref', label: 'Exchange credentials', type: 'text', required: false },
      ],
    },
    goal_templates: [],
  })),
}))

vi.mock('../services/platformCredentials.service', () => ({ upsertPlatformCredential: vi.fn(async () => ({})) }))
vi.mock('../services/exchangeSetup.service', () => ({ upsertExchangeSetup: vi.fn(async () => ({
  exchange_provider: 'delta_exchange_india',
  credential_ref: 'cred-1',
  allowed_coins: ['BTC'],
  default_coin: 'BTC',
  risk_limits: { max_units_per_order: 1 },
})) }))

describe('Exchange credentials visibility', () => {
  it('hides exchange credentials for DMA agents', async () => {
    render(
      <ConfigureAgentPanel
        instance={{ subscription_id: 'sub_1', agent_id: 'AGT-MKT-DMA-001', agent_type_id: 'marketing.digital_marketing.v1', duration: 'monthly', status: 'active', current_period_start: '', current_period_end: '', cancel_at_period_end: false }}
        readOnly={false}
        onSaved={() => {}}
      />
    )

    await waitFor(() => {
      expect(screen.queryByText('Exchange credentials')).not.toBeInTheDocument()
    })
  })

  it('shows exchange credentials for trading agents', async () => {
    const hiredAgents = await import('../services/hiredAgents.service')
    vi.mocked(hiredAgents.getHiredAgentBySubscription).mockResolvedValueOnce({
      hired_instance_id: 'hire_2',
      subscription_id: 'sub_2',
      agent_id: 'AGENT-2',
      agent_type_id: 'trading.share_trader.v1',
      nickname: 'Trader',
      theme: 'default',
      config: {},
      configured: true,
      goals_completed: false,
    } as any)

    render(
      <ConfigureAgentPanel
        instance={{ subscription_id: 'sub_2', agent_id: 'AGT-TRD-001', agent_type_id: 'trading.share_trader.v1', duration: 'monthly', status: 'active', current_period_start: '', current_period_end: '', cancel_at_period_end: false }}
        readOnly={false}
        onSaved={() => {}}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Exchange credentials')).toBeInTheDocument()
    })
  })
})
