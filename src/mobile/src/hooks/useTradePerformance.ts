/**
 * useTradePerformance — fetches trade P&L summary for a hired agent.
 * Calls CP Backend GET /cp/trading/performance/{hiredInstanceId}
 *
 * TRADER-FULL-1 It2 S4
 */
import { useState, useEffect } from 'react';
import apiClient from '@/lib/apiClient';

export interface TradePerformanceSummary {
  hired_instance_id: string;
  trades_count: number;
  pnl_pct_avg: number;
  win_rate: number;
  stop_loss_count: number;
  profit_count: number;
  period_days: number;
  last_stat_date: string | null;
}

export function useTradePerformance(hiredInstanceId: string, periodDays = 90) {
  const [data, setData] = useState<TradePerformanceSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    apiClient
      .get<TradePerformanceSummary>(
        `/api/cp/trading/performance/${hiredInstanceId}?period_days=${periodDays}`
      )
      .then((resp) => {
        if (!cancelled) {
          setData(resp.data);
          setLoading(false);
        }
      })
      .catch((e: Error) => {
        if (!cancelled) {
          setError(e.message ?? 'Failed to load trade performance');
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [hiredInstanceId, periodDays]);

  return { data, loading, error };
}
