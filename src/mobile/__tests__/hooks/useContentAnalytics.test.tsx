/**
 * useContentAnalytics Hook Tests
 */

import { renderHook, waitFor } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

const mockGetContentRecommendations = jest.fn();

jest.mock('../../src/services/contentAnalytics.service', () => ({
  getContentRecommendations: (...args: unknown[]) => mockGetContentRecommendations(...args),
}));

import { useContentAnalytics } from '../../src/hooks/useContentAnalytics';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

const MOCK_RECOMMENDATIONS = {
  top_dimensions: ['educational', 'how-to'],
  best_posting_hours: [9, 14],
  avg_engagement_rate: 5.5,
  total_posts_analyzed: 20,
  recommendation_text: 'Post more educational content.',
};

describe('useContentAnalytics', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns null data when hiredAgentId is undefined', () => {
    const { result } = renderHook(() => useContentAnalytics(undefined), {
      wrapper: createWrapper(),
    });
    expect(result.current.data).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it('fetches content recommendations when hiredAgentId is provided', async () => {
    mockGetContentRecommendations.mockResolvedValue(MOCK_RECOMMENDATIONS);
    const { result } = renderHook(() => useContentAnalytics('ha1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.data).toEqual(MOCK_RECOMMENDATIONS);
    expect(mockGetContentRecommendations).toHaveBeenCalledWith('ha1');
  });

});
