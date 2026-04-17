/**
 * Receipts Service (MOB-PARITY-1 E2-S1)
 *
 * Calls CP Backend receipt endpoints — same contract as CP Frontend.
 */

import apiClient from '../lib/apiClient';

export interface Receipt {
  id: string;
  amount: number;
  currency: string;
  created_at: string;
  order_id: string;
}

export async function listReceipts(): Promise<Receipt[]> {
  const response = await apiClient.get<Receipt[]>('/api/v1/receipts');
  const data = response.data;
  if (Array.isArray(data)) return data;
  if (Array.isArray((data as Record<string, unknown>)?.receipts)) {
    return (data as { receipts: Receipt[] }).receipts;
  }
  return [];
}

export async function getReceiptHtml(receiptId: string): Promise<string> {
  const response = await apiClient.get<string>(`/api/v1/receipts/${receiptId}/html`);
  return response.data;
}
