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

  const activeSubscriptions = subscriptions.filter((subscription) => (subscription.status || '').toLowerCase() === 'active')
  const totalBilled = invoices.reduce((sum, invoice) => sum + (typeof invoice.total_amount === 'number' ? invoice.total_amount : 0), 0)
  const totalReceipted = receipts.reduce((sum, receipt) => sum + (typeof receipt.total_amount === 'number' ? receipt.total_amount : 0), 0)

  return (
    <div className="usage-billing-page">
      <div className="page-header">
        <h1>Usage & Billing</h1>
        <div className="plan-info">
          <div>Next Billing Date: <strong>{nextBillingDate ? formatDate(nextBillingDate) : '—'}</strong></div>
        </div>
      </div>

      <div className="usage-billing-overview">
        <Card className="usage-billing-overview-card usage-billing-overview-card--accent">
          <div className="usage-billing-overview-kicker">Spend Confidence</div>
          <h2>Track what changed before billing surprises you.</h2>
          <p>
            WAOOAW should make cost legible: what is active, what has already been billed,
            and which receipts prove the work you approved or purchased.
          </p>
        </Card>

        <div className="usage-billing-summary-grid">
          <Card className="usage-billing-summary-card">
            <div className="usage-billing-summary-label">Active subscriptions</div>
            <div className="usage-billing-summary-value">{activeSubscriptions.length}</div>
            <div className="usage-billing-summary-note">Live agent contracts currently billing</div>
          </Card>
          <Card className="usage-billing-summary-card">
            <div className="usage-billing-summary-label">Invoices to date</div>
            <div className="usage-billing-summary-value">₹{totalBilled || 0}</div>
            <div className="usage-billing-summary-note">Across {invoices.length} invoice records</div>
          </Card>
          <Card className="usage-billing-summary-card">
            <div className="usage-billing-summary-label">Receipts available</div>
            <div className="usage-billing-summary-value">₹{totalReceipted || 0}</div>
            <div className="usage-billing-summary-note">Across {receipts.length} receipt records</div>
          </Card>
        </div>
      </div>

      <Card className="plan-comparison-card" style={{ padding: '1.25rem' }}>
        <h2>Live subscriptions</h2>
        {loading ? (
          <div style={{ padding: '0.5rem 0' }}>Loading…</div>
        ) : activeSubscriptions.length ? (
          <div style={{ display: 'grid', gap: '0.75rem', paddingTop: '0.5rem', marginBottom: '1rem' }}>
            {activeSubscriptions
              .slice()
              .sort((a, b) => String(a.current_period_end || '').localeCompare(String(b.current_period_end || '')))
              .map((subscription) => (
                <Card key={subscription.subscription_id} style={{ padding: '0.9rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
                    <div>
                      <div style={{ fontWeight: 700 }}>{subscription.agent_id || subscription.subscription_id}</div>
                      <div style={{ opacity: 0.8, fontSize: '0.9rem' }}>
                        Status: {subscription.status || 'active'} · Duration: {subscription.duration || '—'}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '0.82rem', opacity: 0.8 }}>Next billing</div>
                      <div style={{ fontWeight: 700 }}>{subscription.current_period_end ? formatDate(subscription.current_period_end) : '—'}</div>
                    </div>
                  </div>
                </Card>
              ))}
          </div>
        ) : (
          <div style={{ padding: '0.5rem 0 1rem' }}>No active subscriptions yet.</div>
        )}

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

      <Card className="usage-billing-confidence-card">
        <div className="usage-billing-confidence-title">What a confident customer should always know</div>
        <div className="usage-billing-confidence-grid">
          <div>
            <strong>What is live</strong>
            <p>Which agents are active, paused, or in trial right now.</p>
          </div>
          <div>
            <strong>What was charged</strong>
            <p>Invoices should connect to live subscriptions without needing back-and-forth support.</p>
          </div>
          <div>
            <strong>What proves payment</strong>
            <p>Receipts should be one click away whenever you need finance or compliance proof.</p>
          </div>
        </div>
      </Card>
    </div>
  )
}
