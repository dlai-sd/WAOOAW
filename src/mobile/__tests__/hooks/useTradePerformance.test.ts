/**
 * useTradePerformance hook tests (TRADER-FULL-1 It2 S4)
 */
import { renderHook, waitFor } from '@testing-library/react-native';

const mockGet = jest.fn();

jest.mock('@/lib/apiClient', () => ({
  __esModule: true,
  default: {
    get: (...args: unknown[]) => mockGet(...args),
  },
}));

import { useTradePerformance } from '@/hooks/useTradePerformance';

const MOCK_SUMMARY = {
  hired_instance_id: 'trader-001',
  trades_count: 5,
  pnl_pct_avg: 2.1,
  win_rate: 0.6,
  stop_loss_count: 1,
  profit_count: 3,
  period_days: 90,
  last_stat_date: null,
};

describe('useTradePerformance', () => {
  beforeEach(() => jest.clearAllMocks());

  it('calls correct endpoint', async () => {
    mockGet.mockResolvedValue({ data: MOCK_SUMMARY });
    const { result } = renderHook(() => useTradePerformance('trader-001'));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(mockGet).toHaveBeenCalledWith(
      expect.stringContaining('cp/trading/performance/trader-001')
    );
  });

  it('returns data on success', async () => {
    mockGet.mockResolvedValue({ data: MOCK_SUMMARY });
    const { result } = renderHook(() => useTradePerformance('trader-001'));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.data).toEqual(MOCK_SUMMARY);
    expect(result.current.error).toBeNull();
  });

  it('returns error on failure', async () => {
    mockGet.mockRejectedValue(new Error('Network error'));
    const { result } = renderHook(() => useTradePerformance('trader-001'));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('Network error');
    expect(result.current.data).toBeNull();
  });

  it('passes period_days param', async () => {
    mockGet.mockResolvedValue({ data: MOCK_SUMMARY });
    renderHook(() => useTradePerformance('trader-001', 30));

    await waitFor(() => expect(mockGet).toHaveBeenCalled());

    expect(mockGet).toHaveBeenCalledWith(
      expect.stringContaining('period_days=30')
    );
  });
});
