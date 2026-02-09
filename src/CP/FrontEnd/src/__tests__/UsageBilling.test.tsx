import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import UsageBilling from '../pages/authenticated/UsageBilling'

vi.mock('../services/invoices.service', () => {
  return {
    listInvoices: vi.fn(async () => []),
    downloadInvoiceHtml: vi.fn(async () => undefined)
  }
})

vi.mock('../services/receipts.service', () => {
  return {
    listReceipts: vi.fn(async () => []),
    downloadReceiptHtml: vi.fn(async () => undefined)
  }
})

vi.mock('../services/subscriptions.service', () => {
  return {
    listSubscriptions: vi.fn(async () => [])
  }
})

describe('UsageBilling', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', async () => {
    const { container } = render(<UsageBilling />)
    expect(container).toBeTruthy()
    await waitFor(() => {
      expect(screen.getByText('No invoices yet.')).toBeTruthy()
    })
  })

  it('renders component content', async () => {
    render(<UsageBilling />)
    expect(screen.getByText('Usage & Billing')).toBeTruthy()
    expect(screen.getByText('Invoices')).toBeTruthy()
    expect(screen.getByText('Receipts')).toBeTruthy()
    await waitFor(() => {
      expect(screen.getByText('No invoices yet.')).toBeTruthy()
    })
  })

  it('shows empty state when there are no invoices', async () => {
    const subscriptionsServiceModule = await import('../services/subscriptions.service')
    const invoicesServiceModule = await import('../services/invoices.service')
    const receiptsServiceModule = await import('../services/receipts.service')

    vi.mocked(subscriptionsServiceModule.listSubscriptions).mockResolvedValueOnce([])
    vi.mocked(invoicesServiceModule.listInvoices).mockResolvedValueOnce([])
    vi.mocked(receiptsServiceModule.listReceipts).mockResolvedValueOnce([])

    render(<UsageBilling />)

    await waitFor(() => {
      expect(screen.getByText('No invoices yet.')).toBeTruthy()
      expect(screen.getByText('No receipts yet.')).toBeTruthy()
    })
  })

  it('renders invoices and triggers download', async () => {
    const subscriptionsServiceModule = await import('../services/subscriptions.service')
    const invoicesServiceModule = await import('../services/invoices.service')
    const receiptsServiceModule = await import('../services/receipts.service')

    vi.mocked(subscriptionsServiceModule.listSubscriptions).mockResolvedValueOnce([
      {
        subscription_id: 'sub_1',
        agent_id: 'agent_1',
        duration: 'monthly',
        status: 'active',
        current_period_start: '2026-01-01T00:00:00Z',
        current_period_end: '2026-02-01T00:00:00Z',
        cancel_at_period_end: false
      }
    ])

    vi.mocked(invoicesServiceModule.listInvoices).mockResolvedValueOnce([
      {
        invoice_id: 'inv_1',
        invoice_number: 'INV-20260201-0001',
        created_at: '2026-02-01T10:00:00Z',
        order_id: 'order_1',
        subscription_id: 'sub_1',
        currency: 'INR',
        total_amount: 24000,
        tax_type: 'IGST'
      }
    ])

    vi.mocked(receiptsServiceModule.listReceipts).mockResolvedValueOnce([
      {
        receipt_id: 'rct_1',
        receipt_number: 'RCT-20260201-0001',
        created_at: '2026-02-01T10:00:00Z',
        order_id: 'order_1',
        subscription_id: 'sub_1',
        currency: 'INR',
        total_amount: 24000,
        payment_status: 'paid'
      }
    ])

    render(<UsageBilling />)

    await waitFor(() => {
      expect(screen.getByText('INV-20260201-0001')).toBeTruthy()
    })

    expect(screen.getAllByText(/Total:/).length).toBeGreaterThanOrEqual(1)

    fireEvent.click(screen.getAllByText('Download (HTML)')[0])
    await waitFor(() => {
      expect(invoicesServiceModule.downloadInvoiceHtml).toHaveBeenCalledWith('inv_1', 'INV-20260201-0001')
    })

    fireEvent.click(screen.getAllByText('Download (HTML)')[1])
    await waitFor(() => {
      expect(receiptsServiceModule.downloadReceiptHtml).toHaveBeenCalledWith('rct_1', 'RCT-20260201-0001')
    })
  })
})
