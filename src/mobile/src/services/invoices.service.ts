/**
 * Invoices Service (MOB-PARITY-1 E2-S1)
 *
 * Calls CP Backend invoice endpoints — same contract as CP Frontend.
 */

import apiClient from '../lib/apiClient';

export interface Invoice {
  id: string;
  amount: number;
  currency: string;
  status: 'paid' | 'pending' | 'overdue';
  created_at: string;
  pdf_url?: string;
}

export async function listInvoices(): Promise<Invoice[]> {
  const response = await apiClient.get<Invoice[]>('/api/v1/invoices');
  const data = response.data;
  if (Array.isArray(data)) return data;
  if (Array.isArray((data as Record<string, unknown>)?.invoices)) {
    return (data as { invoices: Invoice[] }).invoices;
  }
  return [];
}

export async function getInvoiceHtml(invoiceId: string): Promise<string> {
  const response = await apiClient.get<string>(`/api/v1/invoices/${invoiceId}/html`);
  return response.data;
}
