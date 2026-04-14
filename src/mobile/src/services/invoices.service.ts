/**
 * Invoices Service (MOB-PARITY-1 E2-S1)
 *
 * Calls CP Backend invoice endpoints — same contract as CP Frontend.
 */

import cpApiClient from '../lib/cpApiClient';

export interface Invoice {
  id: string;
  amount: number;
  currency: string;
  status: 'paid' | 'pending' | 'overdue';
  created_at: string;
  pdf_url?: string;
}

export async function listInvoices(): Promise<Invoice[]> {
  const response = await cpApiClient.get<Invoice[]>('/cp/invoices');
  const data = response.data;
  if (Array.isArray(data)) return data;
  if (Array.isArray((data as Record<string, unknown>)?.invoices)) {
    return (data as { invoices: Invoice[] }).invoices;
  }
  return [];
}

export async function getInvoiceHtml(invoiceId: string): Promise<string> {
  const response = await cpApiClient.get<string>(`/cp/invoices/${invoiceId}/html`);
  return response.data;
}
