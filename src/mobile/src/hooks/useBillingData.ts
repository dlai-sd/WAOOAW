/**
 * useBillingData Hook (MOB-PARITY-1 E2-S1)
 *
 * Combines invoices and receipts queries via React Query.
 */

import { useQuery } from '@tanstack/react-query';
import { listInvoices, Invoice } from '../services/invoices.service';
import { listReceipts, Receipt } from '../services/receipts.service';

export interface UseBillingDataResult {
  invoices: Invoice[];
  receipts: Receipt[];
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

export function useBillingData(): UseBillingDataResult {
  const invoicesQuery = useQuery<Invoice[]>({
    queryKey: ['invoices'],
    queryFn: listInvoices,
    staleTime: 1000 * 60 * 5,
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * Math.pow(2, attemptIndex), 10000),
  });

  const receiptsQuery = useQuery<Receipt[]>({
    queryKey: ['receipts'],
    queryFn: listReceipts,
    staleTime: 1000 * 60 * 5,
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * Math.pow(2, attemptIndex), 10000),
  });

  return {
    invoices: invoicesQuery.data ?? [],
    receipts: receiptsQuery.data ?? [],
    isLoading: invoicesQuery.isLoading || receiptsQuery.isLoading,
    error: (invoicesQuery.error || receiptsQuery.error) as Error | null,
    refetch: () => {
      invoicesQuery.refetch();
      receiptsQuery.refetch();
    },
  };
}
