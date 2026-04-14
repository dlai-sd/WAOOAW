/**
 * ContentAnalyticsScreen (MOB-PARITY-1 E3-S1)
 *
 * Shows DMA content performance: summary stat cards + AI recommendations.
 * "Read Insights" FAB uses TTS to speak the summary aloud.
 * VoiceFAB lets the customer trigger readback via voice command.
 */

import React, { useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { useRoute, RouteProp } from '@react-navigation/native';
import { useTheme } from '../../hooks/useTheme';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorView } from '../../components/ErrorView';
import { EmptyState } from '../../components/EmptyState';
import { VoiceFAB } from '../../components/voice/VoiceFAB';
import { useContentAnalytics } from '../../hooks/useContentAnalytics';
import { useTextToSpeech } from '../../hooks/useTextToSpeech';
import { useAgentVoiceOverlay } from '../../hooks/useAgentVoiceOverlay';
import type { MyAgentsStackParamList } from '../../navigation/types';

type ContentAnalyticsRouteProp = RouteProp<MyAgentsStackParamList, 'ContentAnalytics'>;

// ─── Stat Card ────────────────────────────────────────────────────────────────

interface StatCardProps {
  label: string;
  value: string;
  testID?: string;
}

function StatCard({ label, value, testID }: StatCardProps) {
  const { colors, spacing, typography } = useTheme();
  return (
    <View
      testID={testID}
      style={[
        styles.statCard,
        {
          backgroundColor: colors.card,
          borderRadius: spacing.md,
          padding: spacing.md,
          flex: 1,
          margin: spacing.xs,
          alignItems: 'center',
        },
      ]}
    >
      <Text
        style={{
          color: colors.neonCyan,
          fontSize: 22,
          fontFamily: typography.fontFamily.bodyBold,
          marginBottom: spacing.xs,
        }}
        numberOfLines={1}
        adjustsFontSizeToFit
      >
        {value}
      </Text>
      <Text
        style={{
          color: colors.textSecondary,
          fontSize: 11,
          fontFamily: typography.fontFamily.body,
          textAlign: 'center',
        }}
      >
        {label}
      </Text>
    </View>
  );
}

// ─── ContentAnalyticsScreen ───────────────────────────────────────────────────

export function ContentAnalyticsScreen() {
  const { colors, spacing, typography } = useTheme();
  const route = useRoute<ContentAnalyticsRouteProp>();
  const { hiredAgentId } = route.params ?? {};

  const { data, isLoading, error, refetch } = useContentAnalytics(hiredAgentId);
  const { speak, isSpeaking, stop } = useTextToSpeech();

  const readInsights = useCallback(async () => {
    if (isSpeaking) {
      await stop();
      return;
    }
    const script = data
      ? `You have ${data.total_posts_analyzed} posts analyzed with ${data.avg_engagement_rate.toFixed(1)} percent average engagement. Top dimensions are ${data.top_dimensions.join(', ')}. Recommendation: ${data.recommendation_text}`
      : 'No insights available yet.';
    await speak(script);
  }, [data, isSpeaking, speak, stop]);

  const { isListening, toggle, isAvailable } = useAgentVoiceOverlay({
    'read insights': () => readInsights(),
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorView message="Failed to load analytics" onRetry={refetch} />;
  if (!data) return <EmptyState message="No analytics data yet" icon="📊" />;

  return (
    <SafeAreaView
      style={[styles.safeArea, { backgroundColor: colors.black }]}
      testID="content-analytics-screen"
    >
      <ScrollView
        contentContainerStyle={{
          paddingHorizontal: spacing.screenPadding?.horizontal ?? spacing.lg,
          paddingTop: spacing.lg,
          paddingBottom: 100,
        }}
      >
        {/* Header */}
        <Text
          style={{
            color: colors.neonCyan,
            fontSize: 11,
            fontFamily: typography.fontFamily.bodyBold,
            textTransform: 'uppercase',
            letterSpacing: 1,
            marginBottom: spacing.xs,
          }}
        >
          Performance
        </Text>
        <Text
          style={{
            color: colors.textPrimary,
            fontSize: 26,
            fontFamily: typography.fontFamily.display,
            marginBottom: spacing.xl,
          }}
        >
          Content Analytics
        </Text>

        {/* Stat Cards row 1 */}
        <View style={{ flexDirection: 'row', marginBottom: spacing.sm }}>
          <StatCard
            testID="stat-total-posts"
            label="Posts Analyzed"
            value={String(data.total_posts_analyzed)}
          />
          <StatCard
            testID="stat-engagement-rate"
            label="Avg Engagement"
            value={`${data.avg_engagement_rate.toFixed(1)}%`}
          />
        </View>

        {/* Stat Cards row 2 */}
        <View style={{ flexDirection: 'row', marginBottom: spacing.xl }}>
          <StatCard
            testID="stat-top-dimensions"
            label="Top Dimensions"
            value={data.top_dimensions.slice(0, 2).join(', ') || '—'}
          />
          <StatCard
            testID="stat-posting-hours"
            label="Best Hours"
            value={
              data.best_posting_hours.length > 0
                ? data.best_posting_hours.slice(0, 3).map((h) => `${h}:00`).join(', ')
                : '—'
            }
          />
        </View>

        {/* Recommendations */}
        <Text
          style={{
            color: colors.textPrimary,
            fontSize: 18,
            fontFamily: typography.fontFamily.bodyBold,
            marginBottom: spacing.md,
          }}
        >
          AI Recommendation
        </Text>
        <View
          testID="recommendation-block"
          style={{
            backgroundColor: colors.card,
            borderRadius: spacing.md,
            padding: spacing.lg,
            marginBottom: spacing.xl,
          }}
        >
          <Text
            style={{
              color: colors.textPrimary,
              fontSize: 14,
              fontFamily: typography.fontFamily.body,
              lineHeight: 22,
            }}
          >
            {data.recommendation_text}
          </Text>
        </View>

        {/* Read Insights Button */}
        <TouchableOpacity
          testID="read-insights-btn"
          onPress={readInsights}
          style={[
            styles.readBtn,
            {
              backgroundColor: isSpeaking ? colors.error + '20' : colors.neonCyan + '20',
              borderRadius: spacing.md,
              padding: spacing.md,
              alignItems: 'center',
            },
          ]}
        >
          <Text
            style={{
              color: isSpeaking ? colors.error : colors.neonCyan,
              fontSize: 15,
              fontFamily: typography.fontFamily.bodyBold,
            }}
          >
            {isSpeaking ? '⏹ Stop Reading' : '🔊 Read Insights'}
          </Text>
        </TouchableOpacity>
      </ScrollView>

      {/* Voice FAB */}
      {isAvailable && (
        <VoiceFAB
          isListening={isListening}
          onPress={toggle}
          testID="voice-fab"
          position="bottom-right"
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1 },
  statCard: {},
  readBtn: {},
});
