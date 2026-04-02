import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'

import { PublishHistoryPanel } from '../pages/authenticated/MyAgents'

vi.mock('../services/publishReceipts.service', () => ({
  listPublishReceipts: vi.fn(async () => [
    {
      id: 'receipt-1',
      hired_instance_id: 'hire_1',
      platform_key: 'youtube',
      published_at: '2026-04-01T12:00:00Z',
      status: 'success',
      platform_url: 'https://youtube.com/watch?v=abc123',
    },
    {
      id: 'receipt-2',
      hired_instance_id: 'hire_1',
      platform_key: 'youtube',
      published_at: '2026-04-01T13:00:00Z',
      status: 'failed',
      error_message: 'Upload failed',
    },
  ]),
}))

describe('PublishHistoryPanel', () => {
  it('renders publish receipts with success and failed badges', async () => {
    render(
      <PublishHistoryPanel
        instance={{ hired_instance_id: 'hire_1', subscription_id: 'sub_1', agent_id: 'AGT-MKT-DMA-001', duration: 'monthly', status: 'active', current_period_start: '', current_period_end: '', cancel_at_period_end: false }}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Publish History')).toBeInTheDocument()
    })
    expect(screen.getAllByText('youtube')).toHaveLength(2)
    expect(screen.getByTestId('publish-receipt-status-success')).toBeInTheDocument()
    expect(screen.getByTestId('publish-receipt-status-failed')).toBeInTheDocument()
  })

  it('renders the empty state when there is no publish history', async () => {
    const receipts = await import('../services/publishReceipts.service')
    vi.mocked(receipts.listPublishReceipts).mockResolvedValueOnce([])

    render(
      <PublishHistoryPanel
        instance={{ hired_instance_id: 'hire_2', subscription_id: 'sub_2', agent_id: 'AGT-MKT-DMA-001', duration: 'monthly', status: 'active', current_period_start: '', current_period_end: '', cancel_at_period_end: false }}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('No publish history yet')).toBeInTheDocument()
    })
  })

  it('renders an error state when publish history fails to load', async () => {
    const receipts = await import('../services/publishReceipts.service')
    vi.mocked(receipts.listPublishReceipts).mockRejectedValueOnce(new Error('boom'))

    render(
      <PublishHistoryPanel
        instance={{ hired_instance_id: 'hire_3', subscription_id: 'sub_3', agent_id: 'AGT-MKT-DMA-001', duration: 'monthly', status: 'active', current_period_start: '', current_period_end: '', cancel_at_period_end: false }}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('boom')).toBeInTheDocument()
    })
  })
})
