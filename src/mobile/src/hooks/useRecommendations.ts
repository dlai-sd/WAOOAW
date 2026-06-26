/**
 * useRecommendations — fetches RSI threshold recommendations for a hired agent.
 * Calls CP Backend GET /cp/trading/recommendations/{hiredInstanceId}
 *
 * TRADER-FULL-1 It2 S5
 */
import { useState, useEffect } from 'react';
import apiClient from '@/lib/apiClient';

export interface TradeRecommendation {
  hired_instance_id: string;
  suggested_rsi_buy_threshold: number;
  suggested_rsi_sell_threshold: number;
  current_rsi_buy_threshold: number;
  current_rsi_sell_threshold: number;
  confidence: number;
  rationale: string;
  sample_size: number;
  engine: string;
}

export function useRecommendations(hiredInstanceId: string) {
  const [data, setData] = useState<TradeRecommendation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    apiClient
      .get<TradeRecommendation>(
        `/api/cp/trading/recommendations/${hiredInstanceId}`
      )
      .then((resp) => {
        if (!cancelled) {
          setData(resp.data);
          setLoading(false);
        }
      })
      .catch((e: Error) => {
        if (!cancelled) {
          setError(e.message ?? 'Failed to load recommendations');
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [hiredInstanceId]);

  return { data, loading, error };
}
