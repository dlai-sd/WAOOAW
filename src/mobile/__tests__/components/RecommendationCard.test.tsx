/**
 * RecommendationCard tests (TRADER-FULL-1 It2 S5)
 */
import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react-native';
import {
  RecommendationCard,
  RecommendationCardLoading,
} from '@/components/RecommendationCard';

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

const MOCK_RECOMMENDATION = {
  hired_instance_id: 'trader-001',
  current_rsi_buy_threshold: 30,
  current_rsi_sell_threshold: 70,
  suggested_rsi_buy_threshold: 35,
  suggested_rsi_sell_threshold: 65,
  confidence: 0.75,
  rationale: 'BUY accuracy 40% over 10 signals. Raising BUY threshold.',
  sample_size: 15,
  engine: 'rule_based',
};

describe('RecommendationCard', () => {
  const mockApply = jest.fn();
  const mockDismiss = jest.fn();

  beforeEach(() => jest.clearAllMocks());

  it('renders rationale text', () => {
    render(
      <RecommendationCard
        recommendation={MOCK_RECOMMENDATION}
        onApply={mockApply}
        onDismiss={mockDismiss}
      />
    );
    expect(
      screen.getByText('BUY accuracy 40% over 10 signals. Raising BUY threshold.')
    ).toBeTruthy();
  });

  it('renders confidence bar testID', () => {
    render(
      <RecommendationCard
        recommendation={MOCK_RECOMMENDATION}
        onApply={mockApply}
        onDismiss={mockDismiss}
      />
    );
    expect(screen.getByTestId('confidence-fill')).toBeTruthy();
  });

  it('apply button fires onApply callback with suggested thresholds', () => {
    render(
      <RecommendationCard
        recommendation={MOCK_RECOMMENDATION}
        onApply={mockApply}
        onDismiss={mockDismiss}
      />
    );
    fireEvent.press(screen.getByTestId('rec-apply-btn'));
    expect(mockApply).toHaveBeenCalledWith('trader-001', {
      rsi_buy: 35,
      rsi_sell: 65,
    });
  });

  it('dismiss button fires onDismiss callback', () => {
    render(
      <RecommendationCard
        recommendation={MOCK_RECOMMENDATION}
        onApply={mockApply}
        onDismiss={mockDismiss}
      />
    );
    fireEvent.press(screen.getByTestId('rec-dismiss-btn'));
    expect(mockDismiss).toHaveBeenCalled();
  });

  it('renders recommendation-card testID', () => {
    render(
      <RecommendationCard
        recommendation={MOCK_RECOMMENDATION}
        onApply={mockApply}
        onDismiss={mockDismiss}
      />
    );
    expect(screen.getByTestId('recommendation-card')).toBeTruthy();
  });
});

describe('RecommendationCardLoading', () => {
  it('renders loading state without crash', () => {
    render(<RecommendationCardLoading />);
    expect(screen.getByTestId('recommendation-loading')).toBeTruthy();
    expect(screen.getByText('Loading…')).toBeTruthy();
  });
});
