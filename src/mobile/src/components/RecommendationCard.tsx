/**
 * RecommendationCard — RSI threshold recommendation for Share Trader agent (TRADER-FULL-1 It2 S5)
 *
 * Shows:
 * - Rationale text
 * - Confidence bar (cyan, width = confidence * 100%)
 * - "Apply" button (green) → calls onApply with suggested thresholds
 * - "Dismiss" button (outline)
 */
import React from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useTheme } from '@/hooks/useTheme';
import type { TradeRecommendation } from '@/hooks/useRecommendations';

export interface SuggestedThresholds {
  rsi_buy: number;
  rsi_sell: number;
}

interface Props {
  recommendation: TradeRecommendation;
  onApply: (hiredInstanceId: string, thresholds: SuggestedThresholds) => void;
  onDismiss: () => void;
}

export function RecommendationCard({ recommendation, onApply, onDismiss }: Props) {
  const { colors, typography } = useTheme();

  return (
    <View
      style={[styles.card, { borderColor: colors.textSecondary + '20' }]}
      testID="recommendation-card"
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
        Agent Recommendation
      </Text>

      {/* Rationale */}
      <Text
        style={[
          styles.rationale,
          { color: colors.textSecondary, fontFamily: typography.fontFamily.body },
        ]}
        testID="rec-rationale"
      >
        {recommendation.rationale}
      </Text>

      {/* Confidence bar */}
      <View style={styles.confidenceTrack} testID="confidence-track">
        <View
          style={[
            styles.confidenceFill,
            { width: `${recommendation.confidence * 100}%` as unknown as number },
          ]}
          testID="confidence-fill"
        />
      </View>
      <Text style={styles.confidenceLabel}>
        Confidence: {Math.round(recommendation.confidence * 100)}%
      </Text>

      {/* Suggested thresholds */}
      <View style={styles.thresholdRow}>
        <Text style={[styles.thresholdText, { color: colors.textPrimary }]}>
          RSI Buy: {recommendation.current_rsi_buy_threshold} →{' '}
          <Text style={{ color: '#00f2fe' }}>
            {recommendation.suggested_rsi_buy_threshold}
          </Text>
        </Text>
        <Text style={[styles.thresholdText, { color: colors.textPrimary }]}>
          RSI Sell: {recommendation.current_rsi_sell_threshold} →{' '}
          <Text style={{ color: '#00f2fe' }}>
            {recommendation.suggested_rsi_sell_threshold}
          </Text>
        </Text>
      </View>

      {/* Action buttons */}
      <View style={styles.buttonsRow}>
        <TouchableOpacity
          style={[styles.btn, { backgroundColor: '#10b98122' }]}
          onPress={() =>
            onApply(recommendation.hired_instance_id, {
              rsi_buy: recommendation.suggested_rsi_buy_threshold,
              rsi_sell: recommendation.suggested_rsi_sell_threshold,
            })
          }
          accessibilityLabel="Apply recommendation"
          testID="rec-apply-btn"
        >
          <Text style={{ color: '#10b981', fontSize: 13, fontWeight: '600' }}>
            ✓ Apply
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.btn, styles.dismissBtn]}
          onPress={onDismiss}
          accessibilityLabel="Dismiss recommendation"
          testID="rec-dismiss-btn"
        >
          <Text style={{ color: '#71717a', fontSize: 13, fontWeight: '600' }}>
            Dismiss
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

export function RecommendationCardLoading() {
  return (
    <View style={styles.card} testID="recommendation-loading">
      <ActivityIndicator color="#00f2fe" />
      <Text style={styles.confidenceLabel}>Loading…</Text>
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
  title: { fontSize: 14, marginBottom: 8 },
  rationale: { fontSize: 13, marginBottom: 12, lineHeight: 18 },
  confidenceTrack: {
    height: 6,
    borderRadius: 3,
    backgroundColor: '#27272a',
    marginBottom: 4,
    overflow: 'hidden',
  },
  confidenceFill: {
    height: 6,
    backgroundColor: '#00f2fe',
    borderRadius: 3,
  },
  confidenceLabel: { fontSize: 11, color: '#71717a', marginBottom: 10 },
  thresholdRow: { gap: 4, marginBottom: 14 },
  thresholdText: { fontSize: 13 },
  buttonsRow: { flexDirection: 'row', gap: 10 },
  btn: {
    flex: 1,
    borderRadius: 8,
    paddingVertical: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dismissBtn: {
    borderWidth: 1,
    borderColor: '#27272a',
  },
});
