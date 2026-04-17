/**
 * Content Analytics Service Tests (MOB-PARITY-1 E3-S1)
 */

const mockCpGet = jest.fn();

jest.mock('../src/lib/apiClient', () => ({
  __esModule: true,
  default: {
    get: (...args: unknown[]) => mockCpGet(...args),
    post: jest.fn(),
  },
}));

import { getContentRecommendations, ContentRecommendation } from '../src/services/contentAnalytics.service';

describe('contentAnalytics.service', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns typed ContentRecommendation object', async () => {
    const mockData: ContentRecommendation = {
      top_dimensions: ['educational', 'how-to'],
      best_posting_hours: [9, 14],
      avg_engagement_rate: 5.5,
      total_posts_analyzed: 20,
      recommendation_text: 'Post more educational content.',
    };
    mockCpGet.mockResolvedValue({ data: mockData });

    const result = await getContentRecommendations('ha1');

    expect(result).toEqual(mockData);
    expect(mockCpGet).toHaveBeenCalledWith('/api/v1/hired-agents/ha1/content-recommendations');
  });
});
