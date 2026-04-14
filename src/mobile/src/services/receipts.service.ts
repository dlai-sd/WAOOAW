/**
 * Receipts Service (MOB-PARITY-1 E2-S1)
 *
 * Calls CP Backend receipt endpoints — same contract as CP Frontend.
 */

import cpApiClient from '../lib/cpApiClient';

export interface Receipt {
  id: string;
  amount: number;
  currency: string;
  created_at: string;
  order_id: string;
}

export async function listReceipts(): Promise<Receipt[]> {
  const response = await cpApiClient.get<Receipt[]>('/cp/receipts');
  const data = response.data;
  if (Array.isArray(data)) return data;
  if (Array.isArray((data as Record<string, unknown>)?.receipts)) {
    return (data as { receipts: Receipt[] }).receipts;
  }
  return [];
}

export async function getReceiptHtml(receiptId: string): Promise<string> {
  const response = await cpApiClient.get<string>(`/cp/receipts/${receiptId}/html`);
  return response.data;
}
