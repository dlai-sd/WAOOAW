/**
 * ContentAnalyticsScreen Tests (MOB-PARITY-1 E3-S1)
 */

import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';

// ─── Mock theme ───────────────────────────────────────────────────────────────

const mockTheme = {
  colors: {
    black: '#0a0a0a', neonCyan: '#00f2fe', neonPurple: '#667eea',
    textPrimary: '#ffffff', textSecondary: '#a1a1aa', card: '#18181b',
    error: '#ef4444', success: '#10b981', warning: '#f59e0b',
    border: '#374151', background: '#0a0a0a',
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

// ─── Mock route ───────────────────────────────────────────────────────────────

jest.mock('@react-navigation/native', () => ({
  useRoute: () => ({ params: { hiredAgentId: 'ha1' } }),
  useNavigation: () => ({ navigate: jest.fn(), goBack: jest.fn() }),
}));

// ─── Mock hooks ───────────────────────────────────────────────────────────────

const mockUseContentAnalytics = jest.fn();
jest.mock('../src/hooks/useContentAnalytics', () => ({
  useContentAnalytics: () => mockUseContentAnalytics(),
}));

const mockSpeak = jest.fn(() => Promise.resolve());
const mockStop = jest.fn(() => Promise.resolve());
jest.mock('../src/hooks/useTextToSpeech', () => ({
  useTextToSpeech: () => ({
    speak: mockSpeak,
    isSpeaking: false,
    stop: mockStop,
    isAvailable: true,
    availableVoices: [],
    queue: jest.fn(),
    pause: jest.fn(),
    resume: jest.fn(),
    clearQueue: jest.fn(),
    queueLength: 0,
    error: null,
  }),
}));

jest.mock('../src/hooks/useAgentVoiceOverlay', () => ({
  useAgentVoiceOverlay: () => ({
    isListening: false,
    toggle: jest.fn(),
    lastCommand: null,
    isAvailable: true,
  }),
}));

jest.mock('../src/components/voice/VoiceFAB', () => {
  const React = require('react');
  const { View } = require('react-native');
  return {
    VoiceFAB: (props: any) => React.createElement(View, { testID: props.testID }),
  };
});

import { ContentAnalyticsScreen } from '../src/screens/agents/ContentAnalyticsScreen';

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('ContentAnalyticsScreen', () => {
  const mockData = {
    top_dimensions: ['educational', 'how-to', 'case-study', 'trends', 'behind-the-scenes'],
    best_posting_hours: [9, 14, 18],
    avg_engagement_rate: 7.2,
    total_posts_analyzed: 42,
    recommendation_text: 'Focus on educational content in the morning hours.',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseContentAnalytics.mockReturnValue({
      data: mockData,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });
  });

  it('renders stat cards with correct data', () => {
    const { getByTestId } = render(<ContentAnalyticsScreen />);
    expect(getByTestId('content-analytics-screen')).toBeTruthy();
    expect(getByTestId('stat-total-posts')).toBeTruthy();
    expect(getByTestId('stat-engagement-rate')).toBeTruthy();
    expect(getByTestId('stat-top-dimensions')).toBeTruthy();
    expect(getByTestId('stat-posting-hours')).toBeTruthy();
  });

  it('renders recommendation text block', () => {
    const { getByTestId, getByText } = render(<ContentAnalyticsScreen />);
    expect(getByTestId('recommendation-block')).toBeTruthy();
    expect(getByText(mockData.recommendation_text)).toBeTruthy();
  });

  it('calls speak when Read Insights is pressed', () => {
    const { getByTestId } = render(<ContentAnalyticsScreen />);
    fireEvent.press(getByTestId('read-insights-btn'));
    expect(mockSpeak).toHaveBeenCalledWith(expect.stringContaining('42 posts analyzed'));
  });

  it('renders EmptyState when data is null', () => {
    mockUseContentAnalytics.mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });
    const { UNSAFE_getByType } = render(<ContentAnalyticsScreen />);
    const { EmptyState } = require('../src/components/EmptyState');
    expect(UNSAFE_getByType(EmptyState)).toBeTruthy();
  });

  it('renders LoadingSpinner when loading', () => {
    mockUseContentAnalytics.mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
      refetch: jest.fn(),
    });
    const { UNSAFE_getByType } = render(<ContentAnalyticsScreen />);
    const { LoadingSpinner } = require('../src/components/LoadingSpinner');
    expect(UNSAFE_getByType(LoadingSpinner)).toBeTruthy();
  });

  it('renders ErrorView when error occurs', () => {
    mockUseContentAnalytics.mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error('Analytics unavailable'),
      refetch: jest.fn(),
    });
    const { UNSAFE_getByType } = render(<ContentAnalyticsScreen />);
    const { ErrorView } = require('../src/components/ErrorView');
    expect(UNSAFE_getByType(ErrorView)).toBeTruthy();
  });

  it('renders VoiceFAB', () => {
    const { getByTestId } = render(<ContentAnalyticsScreen />);
    expect(getByTestId('voice-fab')).toBeTruthy();
  });
});
