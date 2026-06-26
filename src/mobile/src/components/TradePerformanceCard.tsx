/**
 * TradePerformanceCard — P&L summary for Share Trader agent (TRADER-FULL-1 It2 S4)
 */
import React from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { useTheme } from '@/hooks/useTheme';
import type { TradePerformanceSummary } from '@/hooks/useTradePerformance';

interface Props {
  summary: TradePerformanceSummary;
}

export function TradePerformanceCard({ summary }: Props) {
  const { colors, typography } = useTheme();
  const pnlColor = summary.pnl_pct_avg >= 0 ? '#10b981' : '#ef4444';

  return (
    <View
      style={[styles.card, { borderColor: colors.textSecondary + '20' }]}
      testID="trade-performance-card"
    >
      <Text
        style={[
          styles.title,
          {
            color: colors.textPrimary,
            fontFamily: typography.fontFamily.bodyBold,
          },
        ]}
      >
        Trade Performance ({summary.period_days}d)
      </Text>
      <View style={styles.row}>
        <Stat
          label="Trades"
          value={String(summary.trades_count)}
          color={colors.textPrimary}
          testID="stat-trades"
        />
        <Stat
          label="Avg P&L"
          value={`${summary.pnl_pct_avg.toFixed(1)}%`}
          color={pnlColor}
          testID="stat-pnl"
        />
        <Stat
          label="Win Rate"
          value={`${(summary.win_rate * 100).toFixed(0)}%`}
          color="#00f2fe"
          testID="stat-winrate"
        />
      </View>
    </View>
  );
}

interface StatProps {
  label: string;
  value: string;
  color: string;
  testID?: string;
}

function Stat({ label, value, color, testID }: StatProps) {
  return (
    <View style={styles.stat}>
      <Text style={[styles.value, { color }]} testID={testID}>
        {value}
      </Text>
      <Text style={styles.label}>{label}</Text>
    </View>
  );
}

export function TradePerformanceCardLoading() {
  return (
    <View style={styles.card} testID="trade-performance-loading">
      <ActivityIndicator color="#00f2fe" />
      <Text style={styles.label}>Loading…</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#18181b',
    borderRadius: 16,
    padding: 16,
    marginVertical: 8,
    borderWidth: 1,
  },
  title: { fontSize: 14, marginBottom: 12 },
  row: { flexDirection: 'row', justifyContent: 'space-around' },
  stat: { alignItems: 'center' },
  value: { fontSize: 20, fontWeight: '700' },
  label: { fontSize: 11, color: '#71717a', marginTop: 2 },
});
