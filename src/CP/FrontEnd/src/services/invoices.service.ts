import config from '../config/oauth.config'

const ACCESS_TOKEN_STORAGE_KEY = 'cp_access_token'

export type InvoiceRecord = {
  invoice_id: string
  invoice_number: string
  created_at: string

  order_id: string
  subscription_id: string
  currency: string

  subtotal_amount?: number
  cgst_amount?: number
  sgst_amount?: number
  igst_amount?: number
  total_amount?: number
  tax_type?: string
}

export async function listInvoices(): Promise<InvoiceRecord[]> {
  const url = new URL('/cp/invoices', config.apiBaseUrl)

  const token = localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY)
  const res = await fetch(url.toString(), {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    }
  })

  if (!res.ok) {
    throw new Error(`Failed to load invoices (${res.status})`)
  }

  const body = (await res.json()) as { invoices?: InvoiceRecord[] }
  return body.invoices || []
}

function filenameFromContentDisposition(headerValue: string | null): string | null {
  if (!headerValue) return null

  // Basic support for: attachment; filename=INV-20260101-0001.html
  const match = /filename\*=UTF-8''([^;]+)|filename=([^;]+)/i.exec(headerValue)
  const raw = (match?.[1] || match?.[2] || '').trim()
  if (!raw) return null
  return decodeURIComponent(raw.replace(/^"|"$/g, ''))
}

export async function downloadInvoiceHtml(invoiceId: string, invoiceNumber?: string): Promise<void> {
  const url = new URL(`/cp/invoices/${encodeURIComponent(invoiceId)}/html`, config.apiBaseUrl)

  const token = localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY)
  const res = await fetch(url.toString(), {
    method: 'GET',
    headers: {
      Accept: 'text/html',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    }
  })

  if (!res.ok) {
    throw new Error(`Failed to download invoice (${res.status})`)
  }

  const html = await res.text()
  const contentDisposition = res.headers.get('content-disposition')
  const filename =
    filenameFromContentDisposition(contentDisposition) ||
    (invoiceNumber ? `${invoiceNumber}.html` : `invoice-${invoiceId}.html`)

  const blob = new Blob([html], { type: 'text/html' })
  const objectUrl = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = objectUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()

  URL.revokeObjectURL(objectUrl)
}
