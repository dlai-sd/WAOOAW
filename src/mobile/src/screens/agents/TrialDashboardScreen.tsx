/**
 * Trial Dashboard Screen (Story 2.13)
 * 
 * Shows trial progress, status, and actions for an agent in trial
 * Uses useTrialStatusBySubscription() and useHiredAgent() hooks
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  SafeAreaView,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { useTheme } from '@/hooks/useTheme';
import { useHiredAgent } from '@/hooks/useHiredAgents';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { ErrorView } from '@/components/ErrorView';
import type { MyAgentsStackScreenProps } from '@/navigation/types';

type Props = MyAgentsStackScreenProps<'TrialDashboard'>;

export const TrialDashboardScreen = ({ navigation, route }: Props) => {
  const { colors, spacing, typography } = useTheme();
  const { trialId } = route.params;

  // Fetch agent details using subscription_id (trialId is subscription_id)
  const {
    data: agent,
    isLoading,
    error,
    refetch,
  } = useHiredAgent(trialId);

  // Pull-to-refresh
  const [refreshing, setRefreshing] = React.useState(false);
  const onRefresh = React.useCallback(async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  }, [refetch]);

  // Calculate days remaining
  const getDaysRemaining = () => {
    if (!agent?.trial_end_at) return null;
    const now = new Date();
    const endDate = new Date(agent.trial_end_at);
    const diffTime = endDate.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const daysRemaining = getDaysRemaining();

  // Get progress percentage (7-day trial)
  const getProgressPercentage = () => {
    if (!agent?.trial_start_at || !agent?.trial_end_at) return 0;
    const start = new Date(agent.trial_start_at).getTime();
    const end = new Date(agent.trial_end_at).getTime();
    const now = Date.now();
    const total = end - start;
    const elapsed = now - start;
    const percentage = Math.min(Math.max((elapsed / total) * 100, 0), 100);
    return percentage;
  };

  const progressPercentage = getProgressPercentage();

  // Navigate to agent detail
  const handleViewAgent = () => {
    if (agent?.agent_id) {
      navigation.navigate('AgentDetail', { agentId: agent.agent_id });
    }
  };

  // Navigate back to My Agents
  const handleClose = () => {
    navigation.goBack();
  };

  // Loading state
  if (isLoading && !refreshing) {
    return (
      <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.black }]}>
        <LoadingSpinner message="Loading trial details..." />
      </SafeAreaView>
    );
  }

  // Error state
  if (error && !refreshing) {
    return (
      <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.black }]}>
        <ErrorView
          message={error.message || 'Failed to load trial details'}
          onRetry={refetch}
        />
      </SafeAreaView>
    );
  }

  // No agent data
  if (!agent) {
    return (
      <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.black }]}>
        <View style={[styles.container, { padding: spacing.xl }]}>
          <Text style={{ color: colors.textPrimary, fontSize: 18, textAlign: 'center' }}>
            Trial not found
          </Text>
          <TouchableOpacity
            style={[
              styles.button,
              {
                backgroundColor: colors.neonCyan,
                marginTop: spacing.lg,
                borderRadius: spacing.md,
                padding: spacing.md,
              },
            ]}
            onPress={handleClose}
          >
            <Text style={{ color: colors.black, fontFamily: typography.fontFamily.bodyBold }}>
              Back to My Agents
            </Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  // Determine status badge
  const getStatusBadge = () => {
    if (agent.trial_status === 'active') {
      if (daysRemaining !== null && daysRemaining <= 0) {
        return { text: 'Trial Ended', color: colors.warning, icon: '⚠️' };
      }
      return { text: 'Active Trial', color: colors.success, icon: '✓' };
    }
    if (agent.trial_status === 'expired') {
      return { text: 'Trial Expired', color: colors.warning, icon: '⚠️' };
    }
    if (agent.trial_status === 'converted') {
      return { text: 'Converted to Paid', color: colors.success, icon: '✓' };
    }
    if (agent.trial_status === 'canceled') {
      return { text: 'Trial Canceled', color: colors.textSecondary, icon: '✕' };
    }
    return { text: agent.trial_status || 'Unknown', color: colors.textSecondary, icon: '' };
  };

  const statusBadge = getStatusBadge();

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.black }]}>
      <ScrollView
        testID="scroll-view"
        style={styles.scrollView}
        contentContainerStyle={{ paddingBottom: spacing.xl }}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={colors.neonCyan}
            colors={[colors.neonCyan]}
          />
        }
      >
        {/* Header */}
        <View
          style={[
            styles.header,
            {
              paddingHorizontal: spacing.screenPadding.horizontal,
              paddingVertical: spacing.screenPadding.vertical,
              borderBottomWidth: 1,
              borderBottomColor: colors.border,
            },
          ]}
        >
          <View style={styles.headerTop}>
            <TouchableOpacity onPress={handleClose}>
              <Text style={{ color: colors.neonCyan, fontSize: 16 }}>← Back</Text>
            </TouchableOpacity>
            <View
              style={[
                styles.statusBadge,
                {
                  backgroundColor: statusBadge.color + '20',
                  borderRadius: spacing.sm,
                  paddingHorizontal: spacing.md,
                  paddingVertical: spacing.xs,
                },
              ]}
            >
              <Text
                style={{
                  color: statusBadge.color,
                  fontSize: 12,
                  fontFamily: typography.fontFamily.bodyBold,
                }}
              >
                {statusBadge.icon} {statusBadge.text}
              </Text>
            </View>
          </View>

          <Text
            style={{
              color: colors.textPrimary,
              fontSize: 28,
              fontFamily: typography.fontFamily.display,
              marginTop: spacing.md,
            }}
          >
            Trial Dashboard
          </Text>
          <Text
            style={{
              color: colors.textSecondary,
              fontSize: 14,
              fontFamily: typography.fontFamily.body,
              marginTop: spacing.xs,
            }}
          >
            {agent.nickname || agent.agent_id}
          </Text>
        </View>

        {/* Trial Progress Card */}
        {agent.trial_status === 'active' && daysRemaining !== null && (
          <View
            style={[
              styles.progressCard,
              {
                backgroundColor: colors.card,
                margin: spacing.screenPadding.horizontal,
                marginTop: spacing.lg,
                borderRadius: spacing.md,
                padding: spacing.lg,
                borderWidth: 1,
                borderColor: colors.border,
              },
            ]}
          >
            <Text
              style={{
                color: colors.textPrimary,
                fontSize: 18,
                fontFamily: typography.fontFamily.bodyBold,
                marginBottom: spacing.md,
              }}
            >
              Trial Progress
            </Text>

            {/* Progress Bar */}
            <View
              style={[
                styles.progressBarContainer,
                {
                  height: 12,
                  backgroundColor: colors.border,
                  borderRadius: 6,
                  overflow: 'hidden',
                  marginBottom: spacing.md,
                },
              ]}
            >
              <View
                style={[
                  styles.progressBarFill,
                  {
                    width: `${progressPercentage}%`,
                    height: '100%',
                    backgroundColor:
                      daysRemaining <= 1
                        ? colors.error
                        : daysRemaining <= 3
                        ? colors.warning
                        : colors.neonCyan,
                    borderRadius: 6,
                  },
                ]}
              />
            </View>

            {/* Days Remaining */}
            <View style={styles.progressInfo}>
              <View>
                <Text
                  style={{
                    color: colors.textSecondary,
                    fontSize: 14,
                    fontFamily: typography.fontFamily.body,
                  }}
                >
                  Days Remaining
                </Text>
                <Text
                  style={{
                    color:
                      daysRemaining <= 1
                        ? colors.error
                        : daysRemaining <= 3
                        ? colors.warning
                        : colors.success,
                    fontSize: 32,
                    fontFamily: typography.fontFamily.display,
                    marginTop: spacing.xs,
                  }}
                >
                  {daysRemaining <= 0 ? 0 : daysRemaining}
                </Text>
                <Text
                  style={{
                    color: colors.textSecondary,
                    fontSize: 12,
                    fontFamily: typography.fontFamily.body,
                  }}
                >
                  out of 7 days
                </Text>
              </View>

              {/* Trial Dates */}
              <View style={{ alignItems: 'flex-end' }}>
                <Text
                  style={{
                    color: colors.textSecondary,
                    fontSize: 12,
                    fontFamily: typography.fontFamily.body,
                  }}
                >
                  Trial Period
                </Text>
                <Text
                  style={{
                    color: colors.textPrimary,
                    fontSize: 14,
                    fontFamily: typography.fontFamily.bodyBold,
                    marginTop: spacing.xs,
                  }}
                >
                  {new Date(agent.trial_start_at!).toLocaleDateString('en-IN', {
                    month: 'short',
                    day: 'numeric',
                  })}
                  {' – '}
                  {new Date(agent.trial_end_at!).toLocaleDateString('en-IN', {
                    month: 'short',
                    day: 'numeric',
                  })}
                </Text>
              </View>
            </View>
          </View>
        )}

        {/* Agent Info Card */}
        <View
          style={[
            styles.infoCard,
            {
              backgroundColor: colors.card,
              margin: spacing.screenPadding.horizontal,
              marginTop: spacing.lg,
              borderRadius: spacing.md,
              padding: spacing.lg,
              borderWidth: 1,
              borderColor: colors.border,
            },
          ]}
        >
          <Text
            style={{
              color: colors.textPrimary,
              fontSize: 18,
              fontFamily: typography.fontFamily.bodyBold,
              marginBottom: spacing.md,
            }}
          >
            Agent Information
          </Text>

          <View style={styles.infoRow}>
            <Text
              style={{
                color: colors.textSecondary,
                fontSize: 14,
                fontFamily: typography.fontFamily.body,
              }}
            >
              Agent ID
            </Text>
            <Text
              style={{
                color: colors.textPrimary,
                fontSize: 14,
                fontFamily: typography.fontFamily.bodyBold,
              }}
            >
              {agent.agent_id}
            </Text>
          </View>

          {agent.nickname && (
            <View style={[styles.infoRow, { marginTop: spacing.sm }]}>
              <Text
                style={{
                  color: colors.textSecondary,
                  fontSize: 14,
                  fontFamily: typography.fontFamily.body,
                }}
              >
                Nickname
              </Text>
              <Text
                style={{
                  color: colors.textPrimary,
                  fontSize: 14,
                  fontFamily: typography.fontFamily.bodyBold,
                }}
              >
                {agent.nickname}
              </Text>
            </View>
          )}

          <View style={[styles.infoRow, { marginTop: spacing.sm }]}>
            <Text
              style={{
                color: colors.textSecondary,
                fontSize: 14,
                fontFamily: typography.fontFamily.body,
              }}
            >
              Setup Status
            </Text>
            <Text
              style={{
                color: agent.configured ? colors.success : colors.warning,
                fontSize: 14,
                fontFamily: typography.fontFamily.bodyBold,
              }}
            >
              {agent.configured ? '✓ Configured' : '⚠ Needs Setup'}
            </Text>
          </View>

          {agent.configured && (
            <View style={[styles.infoRow, { marginTop: spacing.sm }]}>
              <Text
                style={{
                  color: colors.textSecondary,
                  fontSize: 14,
                  fontFamily: typography.fontFamily.body,
                }}
              >
                Goals Completed
              </Text>
              <Text
                style={{
                  color: agent.goals_completed ? colors.success : colors.textSecondary,
                  fontSize: 14,
                  fontFamily: typography.fontFamily.bodyBold,
                }}
              >
                {agent.goals_completed ? '✓ Yes' : '— Not yet'}
              </Text>
            </View>
          )}
        </View>

        {/* Info Banner */}
        {agent.trial_status === 'active' && (
          <View
            style={[
              styles.infoBanner,
              {
                backgroundColor: colors.neonCyan + '10',
                margin: spacing.screenPadding.horizontal,
                marginTop: spacing.lg,
                borderRadius: spacing.md,
                padding: spacing.lg,
                borderWidth: 1,
                borderColor: colors.neonCyan + '30',
              },
            ]}
          >
            <Text
              style={{
                color: colors.neonCyan,
                fontSize: 16,
                fontFamily: typography.fontFamily.bodyBold,
                marginBottom: spacing.sm,
              }}
            >
              💡 Trial Benefits
            </Text>
            <View style={{ marginTop: spacing.xs }}>
              <Text style={{ color: colors.textPrimary, fontSize: 14, marginBottom: spacing.xs }}>
                ✓ Full access to all agent capabilities
              </Text>
              <Text style={{ color: colors.textPrimary, fontSize: 14, marginBottom: spacing.xs }}>
                ✓ Keep all deliverables even if you cancel
              </Text>
              <Text style={{ color: colors.textPrimary, fontSize: 14, marginBottom: spacing.xs }}>
                ✓ No credit card required during trial
              </Text>
              <Text style={{ color: colors.textPrimary, fontSize: 14 }}>
                ✓ Convert to paid anytime to keep the agent
              </Text>
            </View>
          </View>
        )}

        {/* Action Buttons */}
        <View
          style={[
            styles.actionButtons,
            {
              margin: spacing.screenPadding.horizontal,
              marginTop: spacing.lg,
            },
          ]}
        >
          <TouchableOpacity
            style={[
              styles.primaryButton,
              {
                backgroundColor: colors.neonCyan,
                borderRadius: spacing.md,
                padding: spacing.md,
                alignItems: 'center',
                marginBottom: spacing.md,
              },
            ]}
            onPress={handleViewAgent}
          >
            <Text
              style={{
                color: colors.black,
                fontSize: 16,
                fontFamily: typography.fontFamily.bodyBold,
              }}
            >
              View Agent Details
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.secondaryButton,
              {
                backgroundColor: 'transparent',
                borderWidth: 1,
                borderColor: colors.border,
                borderRadius: spacing.md,
                padding: spacing.md,
                alignItems: 'center',
              },
            ]}
            onPress={handleClose}
          >
            <Text
              style={{
                color: colors.textPrimary,
                fontSize: 16,
                fontFamily: typography.fontFamily.bodyBold,
              }}
            >
              Back to My Agents
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {},
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  statusBadge: {},
  progressCard: {},
  progressBarContainer: {},
  progressBarFill: {},
  progressInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  infoCard: {},
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  infoBanner: {},
  actionButtons: {},
  primaryButton: {},
  secondaryButton: {},
  button: {
    alignItems: 'center',
  },
});
