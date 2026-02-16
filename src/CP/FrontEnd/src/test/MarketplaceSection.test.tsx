import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'
import { waooawLightTheme } from '../theme'
import MarketplaceSection from '../sections/MarketplaceSection'

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
  })

  it('renders static mock agents without API calls', async () => {
    renderWithProvider(<MarketplaceSection />)

    expect(await screen.findByText(/Content Marketing Agent/i)).toBeInTheDocument()
    expect(await screen.findByText(/SDR Agent/i)).toBeInTheDocument()
  })
})
