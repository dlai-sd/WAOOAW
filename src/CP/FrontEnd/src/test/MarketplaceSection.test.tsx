import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'
import { waooawLightTheme } from '../theme'
import MarketplaceSection from '../sections/MarketplaceSection'

const mocks = vi.hoisted(() => {
  return {
    listAgentTypes: vi.fn()
  }
})

vi.mock('../services/plant.service', () => {
  return {
    plantAPIService: {
      listAgentTypes: mocks.listAgentTypes
    }
  }
})

const renderWithProvider = (component: React.ReactElement) => {
  return render(
    <FluentProvider theme={waooawLightTheme}>
      {component}
    </FluentProvider>
  )
}

describe('MarketplaceSection', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    mocks.listAgentTypes.mockReset()
  })

  it('renders exactly two agent types from the Plant catalog', async () => {
    mocks.listAgentTypes.mockResolvedValue([
      {
        agent_type_id: 'marketing.digital_marketing.v1',
        display_name: 'Digital Marketing',
        version: 1
      },
      {
        agent_type_id: 'trading.share_trader.v1',
        display_name: 'Share Trader',
        version: 1
      }
    ])

    renderWithProvider(<MarketplaceSection />)

    expect(await screen.findByText('Digital Marketing')).toBeInTheDocument()
    expect(await screen.findByText('Share Trader')).toBeInTheDocument()

    expect(screen.getByText('marketing.digital_marketing.v1')).toBeInTheDocument()
    expect(screen.getByText('trading.share_trader.v1')).toBeInTheDocument()
  })

  it('fails closed when the catalog size is not exactly two', async () => {
    mocks.listAgentTypes.mockResolvedValue([
      { agent_type_id: 'a', display_name: 'A', version: 1 },
      { agent_type_id: 'b', display_name: 'B', version: 1 },
      { agent_type_id: 'c', display_name: 'C', version: 1 }
    ])

    renderWithProvider(<MarketplaceSection />)

    expect(await screen.findByText('Failed to load agents')).toBeInTheDocument()
    expect(await screen.findByText(/expected exactly 2 agent types/i)).toBeInTheDocument()
  })
})
