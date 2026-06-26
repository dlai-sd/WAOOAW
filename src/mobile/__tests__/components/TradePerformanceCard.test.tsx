/**
 * TradePerformanceCard tests (TRADER-FULL-1 It2 S4)
 */
import React from 'react';
import { render, screen } from '@testing-library/react-native';
import {
  TradePerformanceCard,
  TradePerformanceCardLoading,
} from '@/components/TradePerformanceCard';

jest.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      textPrimary: '#fff',
      textSecondary: '#a1a1aa',
      background: '#0a0a0a',
      surface: '#18181b',
      border: '#27272a',
    },
    typography: {
      fontFamily: { body: 'Inter', bodyBold: 'Inter-Bold', heading: 'Outfit' },
      fontSize: { sm: 12, md: 14, lg: 16 },
    },
    spacing: { xs: 4, sm: 8, md: 16, lg: 24 },
  }),
}));

const POSITIVE_SUMMARY = {
  hired_instance_id: 'trader-001',
  trades_count: 10,
  pnl_pct_avg: 3.5,
  win_rate: 0.6,
  stop_loss_count: 2,
  profit_count: 6,
  period_days: 90,
  last_stat_date: '2026-06-01',
};

const NEGATIVE_SUMMARY = {
  ...POSITIVE_SUMMARY,
  pnl_pct_avg: -1.2,
};

describe('TradePerformanceCard', () => {
  it('renders trades_count', () => {
    render(<TradePerformanceCard summary={POSITIVE_SUMMARY} />);
    expect(screen.getByText('10')).toBeTruthy();
  });

  it('renders pnl_pct_avg', () => {
    render(<TradePerformanceCard summary={POSITIVE_SUMMARY} />);
    expect(screen.getByText('3.5%')).toBeTruthy();
  });

  it('renders win_rate as percentage', () => {
    render(<TradePerformanceCard summary={POSITIVE_SUMMARY} />);
    expect(screen.getByText('60%')).toBeTruthy();
  });

  it('renders positive pnl in green (#10b981)', () => {
    render(<TradePerformanceCard summary={POSITIVE_SUMMARY} />);
    const pnlStat = screen.getByTestId('stat-pnl');
    expect(pnlStat.props.style).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ color: '#10b981' }),
      ])
    );
  });

  it('renders negative pnl in red (#ef4444)', () => {
    render(<TradePerformanceCard summary={NEGATIVE_SUMMARY} />);
    const pnlStat = screen.getByTestId('stat-pnl');
    expect(pnlStat.props.style).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ color: '#ef4444' }),
      ])
    );
  });

  it('renders period_days in title', () => {
    render(<TradePerformanceCard summary={POSITIVE_SUMMARY} />);
    expect(screen.getByText(/Trade Performance \(90d\)/)).toBeTruthy();
  });

  it('renders testID trade-performance-card', () => {
    render(<TradePerformanceCard summary={POSITIVE_SUMMARY} />);
    expect(screen.getByTestId('trade-performance-card')).toBeTruthy();
  });
});

describe('TradePerformanceCardLoading', () => {
  it('renders loading state without crash', () => {
    render(<TradePerformanceCardLoading />);
    expect(screen.getByTestId('trade-performance-loading')).toBeTruthy();
    expect(screen.getByText('Loading…')).toBeTruthy();
  });
});
