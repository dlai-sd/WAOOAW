/**
 * useRecommendations hook tests (TRADER-FULL-1 It2 S5)
 */
import { renderHook, waitFor } from '@testing-library/react-native';

const mockGet = jest.fn();

jest.mock('@/lib/apiClient', () => ({
  __esModule: true,
  default: {
    get: (...args: unknown[]) => mockGet(...args),
  },
}));

import { useRecommendations } from '@/hooks/useRecommendations';

const MOCK_RECOMMENDATION = {
  hired_instance_id: 'trader-001',
  current_rsi_buy_threshold: 30,
  current_rsi_sell_threshold: 70,
  suggested_rsi_buy_threshold: 30,
  suggested_rsi_sell_threshold: 70,
  confidence: 0.0,
  rationale: 'Insufficient trade history (0 trades).',
  sample_size: 0,
  engine: 'rule_based',
};

describe('useRecommendations', () => {
  beforeEach(() => jest.clearAllMocks());

  it('calls correct endpoint', async () => {
    mockGet.mockResolvedValue({ data: MOCK_RECOMMENDATION });
    const { result } = renderHook(() => useRecommendations('trader-001'));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(mockGet).toHaveBeenCalledWith(
      expect.stringContaining('cp/trading/recommendations/trader-001')
    );
  });

  it('returns data on success', async () => {
    mockGet.mockResolvedValue({ data: MOCK_RECOMMENDATION });
    const { result } = renderHook(() => useRecommendations('trader-001'));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.data).toEqual(MOCK_RECOMMENDATION);
    expect(result.current.error).toBeNull();
  });

  it('returns error on failure', async () => {
    mockGet.mockRejectedValue(new Error('Upstream error'));
    const { result } = renderHook(() => useRecommendations('trader-001'));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('Upstream error');
    expect(result.current.data).toBeNull();
  });

  it('starts in loading state', () => {
    mockGet.mockImplementation(() => new Promise(() => {})); // never resolves
    const { result } = renderHook(() => useRecommendations('trader-001'));
    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeNull();
  });
});
