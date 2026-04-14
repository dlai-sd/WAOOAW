/**
 * UsageBillingScreen Tests (MOB-PARITY-1 E2-S1)
 */

import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';

// ─── Shared mock theme ────────────────────────────────────────────────────────

const mockTheme = {
  colors: {
    black: '#0a0a0a',
    neonCyan: '#00f2fe',
    neonPurple: '#667eea',
    textPrimary: '#ffffff',
    textSecondary: '#a1a1aa',
    card: '#18181b',
    error: '#ef4444',
    success: '#10b981',
    warning: '#f59e0b',
    border: '#374151',
    background: '#0a0a0a',
  },
  spacing: {
    xs: 4, sm: 8, md: 16, lg: 24, xl: 32, xxl: 48,
    screenPadding: { horizontal: 20, vertical: 20 },
  },
  typography: {
    fontFamily: {
      display: 'SpaceGrotesk_700Bold',
      body: 'Inter_400Regular',
      bodyBold: 'Inter_600SemiBold',
    },
  },
};

jest.mock('../src/hooks/useTheme', () => ({ useTheme: () => mockTheme }));

const mockUseBillingData = jest.fn();
jest.mock('../src/hooks/useBillingData', () => ({
  useBillingData: () => mockUseBillingData(),
}));

jest.mock('@shopify/flash-list', () => {
  const { FlatList } = require('react-native');
  return { FlashList: FlatList };
});

jest.mock('react-native/Libraries/Linking/Linking', () => ({
  openURL: jest.fn(() => Promise.resolve()),
  createURL: jest.fn((path: string) => `waooaw://${path}`),
}));

import { UsageBillingScreen } from '../src/screens/profile/UsageBillingScreen';

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('UsageBillingScreen', () => {
  const invoices = [
    { id: 'inv1', amount: 1200, currency: 'INR', status: 'paid' as const, created_at: '2026-01-01T00:00:00Z' },
    { id: 'inv2', amount: 800, currency: 'INR', status: 'pending' as const, created_at: '2026-01-02T00:00:00Z' },
  ];
  const receipts = [
    { id: 'rec1', amount: 1200, currency: 'INR', created_at: '2026-01-01T00:00:00Z', order_id: 'ord1' },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseBillingData.mockReturnValue({
      invoices,
      receipts,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });
  });

  it('renders invoice rows and receipt rows', () => {
    const { getByTestId } = render(<UsageBillingScreen />);
    expect(getByTestId('usage-billing-screen')).toBeTruthy();
    expect(getByTestId('invoice-row-inv1')).toBeTruthy();
    expect(getByTestId('invoice-row-inv2')).toBeTruthy();
    expect(getByTestId('receipt-row-rec1')).toBeTruthy();
  });

  it('renders EmptyState for both sections when data is empty', () => {
    mockUseBillingData.mockReturnValue({
      invoices: [],
      receipts: [],
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });
    const { UNSAFE_getAllByType } = render(<UsageBillingScreen />);
    const { EmptyState } = require('../src/components/EmptyState');
    expect(UNSAFE_getAllByType(EmptyState).length).toBeGreaterThanOrEqual(2);
  });

  it('renders LoadingSpinner when loading', () => {
    mockUseBillingData.mockReturnValue({
      invoices: [],
      receipts: [],
      isLoading: true,
      error: null,
      refetch: jest.fn(),
    });
    const { UNSAFE_getByType } = render(<UsageBillingScreen />);
    const { LoadingSpinner } = require('../src/components/LoadingSpinner');
    expect(UNSAFE_getByType(LoadingSpinner)).toBeTruthy();
  });

  it('renders ErrorView when error occurs', () => {
    mockUseBillingData.mockReturnValue({
      invoices: [],
      receipts: [],
      isLoading: false,
      error: new Error('Billing unavailable'),
      refetch: jest.fn(),
    });
    const { UNSAFE_getByType } = render(<UsageBillingScreen />);
    const { ErrorView } = require('../src/components/ErrorView');
    expect(UNSAFE_getByType(ErrorView)).toBeTruthy();
  });

  it('renders Download button for each invoice', () => {
    const { getByTestId } = render(<UsageBillingScreen />);
    expect(getByTestId('invoice-download-inv1')).toBeTruthy();
    expect(getByTestId('invoice-download-inv2')).toBeTruthy();
  });

  it('renders View button for each receipt', () => {
    const { getByTestId } = render(<UsageBillingScreen />);
    expect(getByTestId('receipt-view-rec1')).toBeTruthy();
  });
});
