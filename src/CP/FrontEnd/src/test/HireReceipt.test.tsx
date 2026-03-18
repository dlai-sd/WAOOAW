import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { waooawLightTheme } from '../theme'
import HireReceipt from '../pages/HireReceipt'

const navigateMock = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => navigateMock,
  }
})

function renderReceipt() {
  return render(
    <FluentProvider theme={waooawLightTheme}>
      <MemoryRouter
        initialEntries={[
          '/hire/receipt/ORD-1?subscriptionId=SUB-1&agentId=AGT-MKT-001&agentTypeId=marketing.digital_marketing.v1&catalogVersion=v1&lifecycleState=live_on_cp&agentName=Digital%20Marketing%20Agent',
        ]}
      >
        <Routes>
          <Route path="/hire/receipt/:orderId" element={<HireReceipt />} />
        </Routes>
      </MemoryRouter>
    </FluentProvider>
  )
}

describe('HireReceipt', () => {
  it('routes payment confirmation to My Agents setup instead of the standalone wizard', () => {
    renderReceipt()

    expect(screen.getByText('Order ID')).toBeInTheDocument()
    expect(screen.getByText('ORD-1')).toBeInTheDocument()
    expect(screen.getByText('Subscription ID')).toBeInTheDocument()
    expect(screen.getByText('SUB-1')).toBeInTheDocument()

    fireEvent.click(screen.getByTestId('cp-hire-receipt-continue'))

    expect(navigateMock).toHaveBeenCalledWith('/portal', {
      state: {
        portalEntry: {
          page: 'my-agents',
          agentId: 'AGT-MKT-001',
          source: 'payment-confirmed',
          subscriptionId: 'SUB-1',
          lifecycleState: 'live_on_cp',
          catalogVersion: 'v1',
          agentName: 'Digital Marketing Agent',
          studioStep: 'identity',
          studioFocus: 'identity',
        },
      },
    })
  })
})
