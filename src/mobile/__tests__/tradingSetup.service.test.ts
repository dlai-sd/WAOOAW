/**
 * Trading Setup Service Tests (ST-MVP-1 S1 mobile coverage)
 *
 * Covers all exported functions and the getTaxReport branch (monthly vs quarterly).
 * apiClient is mocked at the module boundary — no network calls.
 */

const mockGet = jest.fn();
const mockPost = jest.fn();

jest.mock('../src/lib/apiClient', () => ({
  __esModule: true,
  default: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
  },
}));

import {
  getTradingSetup,
  sendTradingSetupMessage,
  emergencyStop,
  getTradeHistory,
  getTaxReport,
  type TradingSetupResponse,
  type TradeHistoryResponse,
  type TaxReportResponse,
} from '../src/services/tradingSetup.service';

const HIRED_ID = 'hired-001';

const MOCK_STATE = {
  step: 'done',
  messages: [],
  collected: {},
  validation_status: 'valid' as const,
  configured: true,
  updated_at: '2026-06-28T00:00:00Z',
};

const MOCK_READINESS = {
  configured: true,
  step: 'done',
  has_credentials: true,
  credentials_valid: true,
  has_instrument: true,
  has_rsi_period: true,
  has_risk_limits: true,
};

const MOCK_SETUP_RESPONSE: TradingSetupResponse = {
  hired_instance_id: HIRED_ID,
  state: MOCK_STATE,
  readiness: MOCK_READINESS,
};

describe('tradingSetup.service', () => {
  beforeEach(() => jest.clearAllMocks());

  // ── getTradingSetup ────────────────────────────────────────────────────────

  describe('getTradingSetup', () => {
    it('calls GET /api/cp/trading-setup/{id} and returns response', async () => {
      mockGet.mockResolvedValue({ data: MOCK_SETUP_RESPONSE });

      const result = await getTradingSetup(HIRED_ID);

      expect(result).toEqual(MOCK_SETUP_RESPONSE);
      expect(mockGet).toHaveBeenCalledWith(
        `/api/cp/trading-setup/${HIRED_ID}`
      );
    });

    it('encodes special characters in hiredInstanceId', async () => {
      mockGet.mockResolvedValue({ data: MOCK_SETUP_RESPONSE });
      await getTradingSetup('id with spaces');
      expect(mockGet).toHaveBeenCalledWith('/api/cp/trading-setup/id%20with%20spaces');
    });
  });

  // ── sendTradingSetupMessage ───────────────────────────────────────────────

  describe('sendTradingSetupMessage', () => {
    it('calls POST /api/cp/trading-setup/{id}/message with content body', async () => {
      mockPost.mockResolvedValue({ data: MOCK_SETUP_RESPONSE });

      const result = await sendTradingSetupMessage(HIRED_ID, 'BTC');

      expect(result).toEqual(MOCK_SETUP_RESPONSE);
      expect(mockPost).toHaveBeenCalledWith(
        `/api/cp/trading-setup/${HIRED_ID}/message`,
        { content: 'BTC' },
        expect.objectContaining({ headers: expect.any(Object) })
      );
    });

    it('includes X-Correlation-ID header', async () => {
      mockPost.mockResolvedValue({ data: MOCK_SETUP_RESPONSE });
      await sendTradingSetupMessage(HIRED_ID, 'start');
      const [, , options] = mockPost.mock.calls[0] as [string, unknown, { headers: Record<string, string> }];
      expect(options.headers['X-Correlation-ID']).toBeDefined();
      expect(typeof options.headers['X-Correlation-ID']).toBe('string');
    });
  });

  // ── emergencyStop ─────────────────────────────────────────────────────────

  describe('emergencyStop', () => {
    it('calls POST /api/cp/trading-setup/{id}/emergency-stop', async () => {
      mockPost.mockResolvedValue({ data: { status: 'stopped', stopped_at: '2026-06-28T10:00:00Z' } });

      const result = await emergencyStop(HIRED_ID);

      expect(result.status).toBe('stopped');
      expect(mockPost).toHaveBeenCalledWith(
        `/api/cp/trading-setup/${HIRED_ID}/emergency-stop`,
        {},
        expect.objectContaining({ headers: expect.any(Object) })
      );
    });
  });

  // ── getTradeHistory ───────────────────────────────────────────────────────

  describe('getTradeHistory', () => {
    const MOCK_HISTORY: TradeHistoryResponse = {
      hired_instance_id: HIRED_ID,
      trades: [
        {
          stat_date: '2026-06-01',
          skill_id: 'execute-trade-order',
          trades_count: 3,
          pnl_pct_avg: 1.5,
          win_rate: 0.67,
          stop_loss_count: 1,
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
    };

    it('calls GET with default page and page_size', async () => {
      mockGet.mockResolvedValue({ data: MOCK_HISTORY });

      const result = await getTradeHistory(HIRED_ID);

      expect(result).toEqual(MOCK_HISTORY);
      expect(mockGet).toHaveBeenCalledWith(
        `/api/cp/trading/history/${HIRED_ID}`,
        expect.objectContaining({ params: { page: 1, page_size: 20 } })
      );
    });

    it('passes custom page and pageSize parameters', async () => {
      mockGet.mockResolvedValue({ data: MOCK_HISTORY });

      await getTradeHistory(HIRED_ID, 2, 10);

      expect(mockGet).toHaveBeenCalledWith(
        `/api/cp/trading/history/${HIRED_ID}`,
        expect.objectContaining({ params: { page: 2, page_size: 10 } })
      );
    });
  });

  // ── getTaxReport ──────────────────────────────────────────────────────────

  describe('getTaxReport', () => {
    const MOCK_REPORT: TaxReportResponse = {
      hired_instance_id: HIRED_ID,
      period: 'monthly',
      year: 2026,
      total_trades: 10,
      total_pnl_pct: 3.2,
      profitable_trades: 7,
      loss_trades: 3,
      stop_loss_exits: 2,
      trades: [],
    };

    it('calls GET with monthly period and month param', async () => {
      mockGet.mockResolvedValue({ data: MOCK_REPORT });

      const result = await getTaxReport(HIRED_ID, 2026, 'monthly', 6);

      expect(result).toEqual(MOCK_REPORT);
      expect(mockGet).toHaveBeenCalledWith(
        `/api/cp/trading/tax-report/${HIRED_ID}`,
        expect.objectContaining({
          params: expect.objectContaining({ year: 2026, period: 'monthly', month: 6 }),
        })
      );
    });

    it('calls GET with quarterly period and quarter param', async () => {
      mockGet.mockResolvedValue({ data: { ...MOCK_REPORT, period: 'quarterly' } });

      await getTaxReport(HIRED_ID, 2026, 'quarterly', undefined, 'Q2');

      expect(mockGet).toHaveBeenCalledWith(
        `/api/cp/trading/tax-report/${HIRED_ID}`,
        expect.objectContaining({
          params: expect.objectContaining({ period: 'quarterly', quarter: 'Q2' }),
        })
      );
    });

    it('omits month param when not provided', async () => {
      mockGet.mockResolvedValue({ data: MOCK_REPORT });

      await getTaxReport(HIRED_ID, 2026, 'monthly');

      const [, options] = mockGet.mock.calls[0] as [string, { params: Record<string, unknown> }];
      expect(options.params.month).toBeUndefined();
    });

    it('omits quarter param when not provided', async () => {
      mockGet.mockResolvedValue({ data: MOCK_REPORT });

      await getTaxReport(HIRED_ID, 2026, 'quarterly');

      const [, options] = mockGet.mock.calls[0] as [string, { params: Record<string, unknown> }];
      expect(options.params.quarter).toBeUndefined();
    });
  });
});
