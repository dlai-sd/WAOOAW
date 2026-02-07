import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'
import { waooawLightTheme } from '../theme'

vi.mock('../services/marketingReview.service', () => {
  return {
    listCustomerDraftBatches: vi.fn().mockResolvedValue([
      {
        batch_id: 'b1',
        agent_id: 'AGT-1',
        theme: 'diabetes awareness',
        brand_name: 'Clinic',
        created_at: new Date().toISOString(),
        status: 'pending_review',
        posts: [
          {
            post_id: 'p1',
            channel: 'instagram',
            text: 'Draft text',
            review_status: 'pending_review'
          },
          {
            post_id: 'p2',
            channel: 'facebook',
            text: 'Approved text',
            review_status: 'approved'
          }
        ]
      }
    ]),
    approveDraftPost: vi.fn().mockResolvedValue({ post_id: 'p1', review_status: 'approved', approval_id: 'APR-1' }),
    rejectDraftPost: vi.fn().mockResolvedValue({ post_id: 'p1', decision: 'rejected' }),
    scheduleDraftPost: vi.fn().mockResolvedValue({ post_id: 'p2', execution_status: 'scheduled', scheduled_at: new Date().toISOString() })
  }
})

vi.mock('../services/trading.service', () => {
  return {
    draftTradePlan: vi.fn().mockResolvedValue({
      agent_id: 'AGT-TRD-DELTA-001',
      agent_type: 'trading',
      status: 'draft',
      draft: { coin: 'BTC', units: 1 }
    }),
    approveAndExecuteTrade: vi.fn().mockResolvedValue({
      agent_id: 'AGT-TRD-DELTA-001',
      agent_type: 'trading',
      status: 'draft',
      draft: { intent_action: 'place_order', approval_id: 'APR-1' }
    })
  }
})

const renderWithProvider = (component: React.ReactElement) => {
  return render(
    <FluentProvider theme={waooawLightTheme}>
      {component}
    </FluentProvider>
  )
}

const renderApprovals = async () => {
  const Approvals = (await import('../pages/authenticated/Approvals')).default
  return renderWithProvider(<Approvals />)
}

const textIncludes = (needle: string) => {
  const lowered = needle.toLowerCase().replace(/\s+/g, ' ').trim()
  return (_content: string, node: Element | null) => {
    const normalized = (node?.textContent || '').toLowerCase().replace(/\s+/g, ' ').trim()
    return normalized.includes(lowered)
  }
}

describe('Approvals Component', () => {
  it('renders page title with pending count', async () => {
    await renderApprovals()
    await waitFor(() => {
      expect(screen.getByText('Pending Approvals (1)')).toBeInTheDocument()
    })
  })

  it('displays filter and sort controls', async () => {
    await renderApprovals()
    const selects = await screen.findAllByRole('combobox')
    expect(selects.length).toBeGreaterThan(0)
  })

  it('shows approval requests', async () => {
    await renderApprovals()
    expect(await screen.findByText(/Approve post for INSTAGRAM/i)).toBeInTheDocument()
    expect(screen.getByText('Draft text')).toBeInTheDocument()
  })

  it('shows approved posts ready to schedule', async () => {
    await renderApprovals()
    await waitFor(() => {
      expect(screen.getByText('Approved text')).toBeInTheDocument()
    })
    expect(screen.getByText('🗓 SCHEDULE')).toBeInTheDocument()
  })

  it('displays approval action buttons', async () => {
    await renderApprovals()
    expect(await screen.findByText('✅ APPROVE')).toBeInTheDocument()
    expect(screen.getByText('❌ REJECT')).toBeInTheDocument()
  })
})
