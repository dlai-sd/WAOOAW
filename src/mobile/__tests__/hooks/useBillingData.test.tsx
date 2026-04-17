/**
 * useBillingData Hook Tests
 */

import { renderHook, waitFor, act } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

const mockListInvoices = jest.fn();
const mockListReceipts = jest.fn();

jest.mock('../../src/services/invoices.service', () => ({
  listInvoices: () => mockListInvoices(),
}));

jest.mock('../../src/services/receipts.service', () => ({
  listReceipts: () => mockListReceipts(),
}));

import { useBillingData } from '../../src/hooks/useBillingData';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('useBillingData', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns empty arrays while loading', () => {
    mockListInvoices.mockReturnValue(new Promise(() => {}));
    mockListReceipts.mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useBillingData(), { wrapper: createWrapper() });
    expect(result.current.invoices).toEqual([]);
    expect(result.current.receipts).toEqual([]);
    expect(result.current.isLoading).toBe(true);
  });

  it('returns invoices and receipts on success', async () => {
    const mockInvoices = [{ id: 'inv1', amount: 1000, currency: 'INR', status: 'paid', created_at: '2026-01-01' }];
    const mockReceipts = [{ id: 'rec1', amount: 1000, currency: 'INR', created_at: '2026-01-01', order_id: 'ord1' }];
    mockListInvoices.mockResolvedValue(mockInvoices);
    mockListReceipts.mockResolvedValue(mockReceipts);

    const { result } = renderHook(() => useBillingData(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.invoices).toHaveLength(1);
    expect(result.current.receipts).toHaveLength(1);
    expect(result.current.error).toBeNull();
  });

  it('refetch function can be called', async () => {
    mockListInvoices.mockResolvedValue([]);
    mockListReceipts.mockResolvedValue([]);

    const { result } = renderHook(() => useBillingData(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => {
      result.current.refetch();
    });
    // just confirm it doesn't throw
  });
});
