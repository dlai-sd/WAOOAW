import { useEffect, useMemo, useState } from 'react'
import { Button, Card } from '@fluentui/react-components'

import { downloadInvoiceHtml, listInvoices, type InvoiceRecord } from '../../services/invoices.service'
import { downloadReceiptHtml, listReceipts, type ReceiptRecord } from '../../services/receipts.service'
import { listSubscriptions, type Subscription } from '../../services/subscriptions.service'

export default function UsageBilling() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [invoices, setInvoices] = useState<InvoiceRecord[]>([])
  const [receipts, setReceipts] = useState<ReceiptRecord[]>([])
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([])

  const nextBillingDate = useMemo(() => {
    const active = (subscriptions || []).filter((s) => (s.status || '').toLowerCase() === 'active')
    if (!active.length) return null
    const sorted = [...active].sort((a, b) => (a.current_period_end || '').localeCompare(b.current_period_end || ''))
    return sorted[0]?.current_period_end || null
  }, [subscriptions])

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString()
    } catch {
      return iso
    }
  }

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const [subs, invs, rcts] = await Promise.all([
          listSubscriptions().catch(() => [] as Subscription[]),
          listInvoices().catch(() => [] as InvoiceRecord[]),
          listReceipts().catch(() => [] as ReceiptRecord[])
        ])

        if (cancelled) return
        setSubscriptions(subs || [])
        setInvoices(invs || [])
        setReceipts(rcts || [])
      } catch (e: any) {
        if (!cancelled) setError(e?.message || 'Failed to load billing information')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [])

  const onDownload = async (inv: InvoiceRecord) => {
    setError(null)
    try {
      await downloadInvoiceHtml(inv.invoice_id, inv.invoice_number)
    } catch (e: any) {
      setError(e?.message || 'Failed to download invoice')
    }
  }

  const onDownloadReceipt = async (rct: ReceiptRecord) => {
    setError(null)
    try {
      await downloadReceiptHtml(rct.receipt_id, rct.receipt_number)
    } catch (e: any) {
      setError(e?.message || 'Failed to download receipt')
    }
  }

  return (
    <div className="usage-billing-page">
      <div className="page-header">
        <h1>Usage & Billing</h1>
        <div className="plan-info">
          <div>Next Billing Date: <strong>{nextBillingDate ? formatDate(nextBillingDate) : '—'}</strong></div>
        </div>
      </div>

      <Card className="plan-comparison-card" style={{ padding: '1.25rem' }}>
        <h2>Invoices</h2>
        {loading ? (
          <div style={{ padding: '0.5rem 0' }}>Loading…</div>
        ) : invoices.length ? (
          <div style={{ display: 'grid', gap: '0.75rem', paddingTop: '0.5rem' }}>
            {invoices
              .slice()
              .sort((a, b) => String(b.created_at || '').localeCompare(String(a.created_at || '')))
              .map((inv) => (
                <Card key={inv.invoice_id} style={{ padding: '0.9rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
                    <div>
                      <div style={{ fontWeight: 700 }}>{inv.invoice_number}</div>
                      <div style={{ opacity: 0.8, fontSize: '0.9rem' }}>
                        {inv.created_at ? formatDate(inv.created_at) : '—'} · {inv.currency || 'INR'}
                        {inv.tax_type ? ` · ${inv.tax_type}` : ''}
                      </div>
                      {typeof inv.total_amount === 'number' && (
                        <div style={{ marginTop: '0.25rem' }}>
                          Total: <strong>₹{inv.total_amount}</strong>
                        </div>
                      )}
                    </div>

                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                      <Button appearance="outline" onClick={() => onDownload(inv)}>
                        Download (HTML)
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
          </div>
        ) : (
          <div style={{ padding: '0.5rem 0' }}>No invoices yet.</div>
        )}

        {error && <div style={{ paddingTop: '0.75rem', color: 'var(--colorPaletteRedForeground1)' }}>{error}</div>}
      </Card>

      <Card className="plan-comparison-card" style={{ padding: '1.25rem', marginTop: '1rem' }}>
        <h2>Receipts</h2>
        {loading ? (
          <div style={{ padding: '0.5rem 0' }}>Loading…</div>
        ) : receipts.length ? (
          <div style={{ display: 'grid', gap: '0.75rem', paddingTop: '0.5rem' }}>
            {receipts
              .slice()
              .sort((a, b) => String(b.created_at || '').localeCompare(String(a.created_at || '')))
              .map((rct) => (
                <Card key={rct.receipt_id} style={{ padding: '0.9rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
                    <div>
                      <div style={{ fontWeight: 700 }}>{rct.receipt_number || rct.receipt_id}</div>
                      <div style={{ opacity: 0.8, fontSize: '0.9rem' }}>
                        {rct.created_at ? formatDate(rct.created_at) : '—'} · {rct.currency || 'INR'}
                        {rct.payment_status ? ` · ${rct.payment_status}` : ''}
                      </div>
                      {typeof rct.total_amount === 'number' && (
                        <div style={{ marginTop: '0.25rem' }}>
                          Total: <strong>₹{rct.total_amount}</strong>
                        </div>
                      )}
                    </div>

                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                      <Button appearance="outline" onClick={() => onDownloadReceipt(rct)}>
                        Download (HTML)
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
          </div>
        ) : (
          <div style={{ padding: '0.5rem 0' }}>No receipts yet.</div>
        )}

        {error && <div style={{ paddingTop: '0.75rem', color: 'var(--colorPaletteRedForeground1)' }}>{error}</div>}
      </Card>
    </div>
  )
}
