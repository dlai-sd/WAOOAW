import config from '../config/oauth.config'

const ACCESS_TOKEN_STORAGE_KEY = 'cp_access_token'

export type ReceiptLineItem = {
  description: string
  quantity: number
  unit_amount: number
}

export type ReceiptRecord = {
  receipt_id: string
  receipt_number: string
  created_at: string

  order_id: string
  subscription_id: string
  currency: string

  total_amount?: number
  payment_status?: string
  items?: ReceiptLineItem[]
}

export async function listReceipts(): Promise<ReceiptRecord[]> {
  const url = new URL('/cp/receipts', config.apiBaseUrl)

  const token = localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY)
  const res = await fetch(url.toString(), {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    }
  })

  if (!res.ok) {
    throw new Error(`Failed to load receipts (${res.status})`)
  }

  const body = (await res.json()) as { receipts?: ReceiptRecord[] }
  return body.receipts || []
}

function filenameFromContentDisposition(headerValue: string | null): string | null {
  if (!headerValue) return null

  const match = /filename\*=UTF-8''([^;]+)|filename=([^;]+)/i.exec(headerValue)
  const raw = (match?.[1] || match?.[2] || '').trim()
  if (!raw) return null
  return decodeURIComponent(raw.replace(/^"|"$/g, ''))
}

export async function downloadReceiptHtml(receiptId: string, receiptNumber?: string): Promise<void> {
  const url = new URL(`/cp/receipts/${encodeURIComponent(receiptId)}/html`, config.apiBaseUrl)

  const token = localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY)
  const res = await fetch(url.toString(), {
    method: 'GET',
    headers: {
      Accept: 'text/html',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    }
  })

  if (!res.ok) {
    throw new Error(`Failed to download receipt (${res.status})`)
  }

  const html = await res.text()
  const contentDisposition = res.headers.get('content-disposition')
  const filename =
    filenameFromContentDisposition(contentDisposition) ||
    (receiptNumber ? `${receiptNumber}.html` : `receipt-${receiptId}.html`)

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
