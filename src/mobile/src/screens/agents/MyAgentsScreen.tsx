/**
 * My Agents Screen (Story 2.12)
 * 
 * Shows customer's hired agents and active trials
 * Uses useHiredAgents() and useAgentsInTrial() hooks
 * Includes voice commands for navigation and actions
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  SafeAreaView,
  RefreshControl,
  TouchableOpacity,
  FlatList,
} from 'react-native';
import { useTheme } from '@/hooks/useTheme';
import { useHiredAgents, useAgentsInTrial } from '@/hooks/useHiredAgents';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { ErrorView } from '@/components/ErrorView';
import { VoiceControl } from '@/components/voice/VoiceControl';
import { VoiceHelpModal } from '@/components/voice/VoiceHelpModal';
import { usePerformanceMonitoring } from '@/hooks/usePerformanceMonitoring';
import type { MyAgentInstanceSummary } from '@/types/hiredAgents.types';
import type { MyAgentsStackScreenProps } from '@/navigation/types';

type Props = MyAgentsStackScreenProps<'MyAgents'>;

// ─── Sort options for hired agents list ───────────────────────────────────────

type SortOption = 'attention' | 'alphabetical' | 'recent';

const SORT_OPTIONS: { key: SortOption; label: string }[] = [
  { key: 'attention', label: 'Needs attention' },
  { key: 'alphabetical', label: 'A–Z' },
  { key: 'recent', label: 'Recently active' },
];

function sortAgents(agents: MyAgentInstanceSummary[], sort: SortOption): MyAgentInstanceSummary[] {
  if (sort === 'attention') {
    return [...agents].sort((a, b) => {
      const aScore =
        ((a as any).approvalQueueCount ?? 0) +
        ((a as any).healthStatus === 'degraded' ? 10 : 0);
      const bScore =
        ((b as any).approvalQueueCount ?? 0) +
        ((b as any).healthStatus === 'degraded' ? 10 : 0);
      return bScore - aScore;
    });
  }
  if (sort === 'alphabetical') {
    return [...agents].sort((a, b) => a.agent_id.localeCompare(b.agent_id));
  }
  return agents; // 'recent' = existing order
}

export const MyAgentsScreen = ({ navigation }: Props) => {
  const { colors, spacing, typography } = useTheme();
  const [activeTab, setActiveTab] = React.useState<'trials' | 'hired'>('trials');
  const [showVoiceHelp, setShowVoiceHelp] = React.useState(false);
  const [sortOption, setSortOption] = React.useState<SortOption>('attention');

  // Performance monitoring
  usePerformanceMonitoring('MyAgents');

  // Fetch all hired agents (for hired tab)
  const {
    data: allAgents,
    isLoading: isLoadingAll,
    error: errorAll,
    refetch: refetchAll,
  } = useHiredAgents();

  // Fetch only trial agents (for trials tab)
  const {
    data: trialAgents,
    isLoading: isLoadingTrials,
    error: errorTrials,
    refetch: refetchTrials,
  } = useAgentsInTrial();

  const isLoading = activeTab === 'trials' ? isLoadingTrials : isLoadingAll;
  const error = activeTab === 'trials' ? errorTrials : errorAll;
  const refetch = activeTab === 'trials' ? refetchTrials : refetchAll;

  // Filter hired agents (not in trial)
  const hiredAgents = React.useMemo(() => {
    if (!allAgents) return [];
    return allAgents.filter(agent => agent.trial_status !== 'active');
  }, [allAgents]);

  const agents = activeTab === 'trials'
    ? (trialAgents || [])
    : sortAgents(hiredAgents, sortOption);
  const count = agents.length;

  // Pull-to-refresh handler
  const [refreshing, setRefreshing] = React.useState(false);
  const onRefresh = React.useCallback(async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  }, [refetch]);

  // Navigate to trial dashboard or agent detail
  const handleAgentPress = (agent: MyAgentInstanceSummary) => {
    if (agent.trial_status === 'active' && agent.subscription_id) {
      // In trial - go to trial dashboard
      navigation.navigate('TrialDashboard', {
        trialId: agent.subscription_id,
      });
    } else {
      // Hired - go to agent detail
      navigation.navigate('AgentDetail', { agentId: agent.agent_id });
    }
  };

  // Navigate to discover screen
  const handleDiscoverPress = () => {
    navigation.navigate('Discover' as any);
  };

  // Voice command handlers
  const handleVoiceNavigate = React.useCallback(
    (screen: string) => {
      if (screen === 'Home') {
        navigation.navigate('Home' as any);
      } else if (screen === 'Discover') {
        navigation.navigate('Discover' as any);
      } else if (screen === 'Profile') {
        navigation.navigate('Profile' as any);
      }
    },
    [navigation]
  );

  const handleVoiceAction = React.useCallback(
    (action: string) => {
      if (action === 'refresh') {
        refetch();
      } else if (action === 'showHelp') {
        setShowVoiceHelp(true);
      }
    },
    [refetch]
  );

  const handleVoiceHelp = React.useCallback(() => {
    setShowVoiceHelp(true);
  }, []);

  // Loading state
  if (isLoading && !refreshing) {
    return (
      <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.black }]}>
        <LoadingSpinner message="Loading your agents..." />
      </SafeAreaView>
    );
  }

  // Error state
  if (error && !refreshing) {
    return (
      <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.black }]}>
        <ErrorView
          message={error.message || 'Failed to load agents'}
          onRetry={refetch}
        />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.black }]}>
      {/* Header with Tabs */}
      <View style={[styles.header, { paddingHorizontal: spacing.screenPadding.horizontal, paddingVertical: spacing.screenPadding.vertical }]}>
        <Text
          style={{
            color: colors.neonCyan,
            fontSize: 12,
            fontFamily: typography.fontFamily.bodyBold,
            textTransform: 'uppercase',
            letterSpacing: 1,
            marginBottom: spacing.xs,
          }}
        >
          Runtime cockpit
        </Text>
        <Text
          style={[
            styles.title,
            {
              color: colors.textPrimary,
              fontSize: 28,
              fontFamily: typography.fontFamily.display,
              marginBottom: spacing.md,
            },
          ]}
        >
          My Agents
        </Text>
        <Text
          style={{
            color: colors.textSecondary,
            fontSize: 14,
            fontFamily: typography.fontFamily.body,
            marginBottom: spacing.md,
          }}
        >
          Keep trials, hired agents, and the next decision in one place instead of switching mental models.
        </Text>

        <View style={{ flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.md }}>
          {[
            `${trialAgents?.length || 0} trials`,
            `${hiredAgents.length} hired`,
            `${allAgents?.filter((agent: any) => (agent as any).approvalQueueCount).length || 0} need attention`,
          ].map((pill) => (
            <View
              key={pill}
              style={{
                backgroundColor: colors.card,
                borderRadius: 999,
                paddingHorizontal: spacing.md,
                paddingVertical: spacing.xs,
                borderWidth: 1,
                borderColor: colors.textSecondary + '25',
              }}
            >
              <Text style={{ color: colors.textPrimary, fontSize: 12, fontFamily: typography.fontFamily.bodyBold }}>{pill}</Text>
            </View>
          ))}
        </View>

        {/* Tab Selector */}
        <View
          style={[
            styles.tabContainer,
            {
              backgroundColor: colors.card,
              borderRadius: spacing.md,
              padding: spacing.xs,
              flexDirection: 'row',
              marginBottom: spacing.md,
            },
          ]}
        >
          <TouchableOpacity
            style={[
              styles.tab,
              {
                flex: 1,
                backgroundColor:
                  activeTab === 'trials' ? colors.neonCyan + '30' : 'transparent',
                borderRadius: spacing.sm,
                paddingVertical: spacing.sm,
                alignItems: 'center',
              },
            ]}
            onPress={() => setActiveTab('trials')}
          >
            <Text
              style={[
                styles.tabText,
                {
                  color: activeTab === 'trials' ? colors.neonCyan : colors.textSecondary,
                  fontSize: 14,
                  fontFamily: typography.fontFamily.bodyBold,
                },
              ]}
            >
              Active Trials ({trialAgents?.length || 0})
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[
              styles.tab,
              {
                flex: 1,
                backgroundColor:
                  activeTab === 'hired' ? colors.neonCyan + '30' : 'transparent',
                borderRadius: spacing.sm,
                paddingVertical: spacing.sm,
                alignItems: 'center',
              },
            ]}
            onPress={() => setActiveTab('hired')}
          >
            <Text
              style={[
                styles.tabText,
                {
                  color: activeTab === 'hired' ? colors.neonCyan : colors.textSecondary,
                  fontSize: 14,
                  fontFamily: typography.fontFamily.bodyBold,
                },
              ]}
            >
              Hired ({hiredAgents.length})
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Agent List or Empty State */}
      {count === 0 ? (
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={[
            styles.content,
            { paddingHorizontal: spacing.screenPadding.horizontal, paddingTop: 0 },
          ]}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor={colors.neonCyan}
              colors={[colors.neonCyan]}
            />
          }
        >
          {/* Empty State */}
          <View
            style={[
              styles.emptyState,
              {
                backgroundColor: colors.card,
                borderRadius: spacing.md,
                padding: spacing.xl,
                alignItems: 'center',
              },
            ]}
          >
            <Text style={{ fontSize: 64, marginBottom: spacing.md }}>
              {activeTab === 'trials' ? '⏳' : '🤖'}
            </Text>
            <Text
              style={[
                styles.emptyTitle,
                {
                  color: colors.textPrimary,
                  fontSize: 20,
                  fontFamily: typography.fontFamily.bodyBold,
                  marginBottom: spacing.sm,
                  textAlign: 'center',
                },
              ]}
            >
              {activeTab === 'trials'
                ? 'No Active Trials'
                : 'No agents hired yet'}
            </Text>
            <Text
              style={[
                styles.emptyText,
                {
                  color: colors.textSecondary,
                  fontSize: 14,
                  fontFamily: typography.fontFamily.body,
                  textAlign: 'center',
                  marginBottom: spacing.lg,
                },
              ]}
            >
              {activeTab === 'trials'
                ? 'Start a 7-day trial to see results before hiring'
                : 'Your agents will appear here once you hire one. Try a 7-day free trial — keep everything they build.'}
            </Text>
            <TouchableOpacity
              style={[
                styles.ctaButton,
                {
                  backgroundColor: colors.neonCyan,
                  borderRadius: spacing.md,
                  paddingHorizontal: spacing.xl,
                  paddingVertical: spacing.md,
                },
              ]}
              onPress={handleDiscoverPress}
            >
              <Text
                style={[
                  styles.ctaButtonText,
                  {
                    color: colors.black,
                    fontSize: 16,
                    fontFamily: typography.fontFamily.bodyBold,
                  },
                ]}
              >
                {activeTab === 'trials' ? 'Discover Agents' : 'Browse agents'}
              </Text>
            </TouchableOpacity>
          </View>

          {/* How It Works Section */}
          <View style={[styles.infoSection, { marginTop: spacing.xl }]}>
            <Text
              style={[
                styles.sectionTitle,
                {
                  color: colors.textPrimary,
                  fontSize: 20,
                  fontFamily: typography.fontFamily.bodyBold,
                  marginBottom: spacing.md,
                },
              ]}
            >
              How It Works
            </Text>

            {[
              {
                emoji: '🚀',
                title: 'Start a 7-Day Trial',
                description: 'Try any agent risk-free. See real results on your business.',
              },
              {
                emoji: '📦',
                title: 'Keep All Deliverables',
                description: 'Even if you don\'t hire, you keep everything the agent creates.',
              },
              {
                emoji: '✅',
                title: 'Hire What Works',
                description: 'Only pay for agents that deliver value. No surprises.',
              },
            ].map((step, index) => (
              <View
                key={index}
                style={[
                  styles.stepCard,
                  {
                    backgroundColor: colors.card,
                    borderRadius: spacing.md,
                    padding: spacing.lg,
                    marginBottom: spacing.md,
                  },
                ]}
              >
                <View style={[styles.stepHeader, { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.sm }]}>
                  <View
                    style={[
                      styles.stepIcon,
                      {
                        width: 40,
                        height: 40,
                        borderRadius: 20,
                        backgroundColor: colors.neonCyan + '20',
                        justifyContent: 'center',
                        alignItems: 'center',
                        marginRight: spacing.md,
                      },
                    ]}
                  >
                    <Text style={{ fontSize: 20 }}>{step.emoji}</Text>
                  </View>
                  <Text
                    style={[
                      styles.stepTitle,
                      {
                        color: colors.textPrimary,
                        fontSize: 16,
                        fontFamily: typography.fontFamily.bodyBold,
                        flex: 1,
                      },
                    ]}
                  >
                    {step.title}
                  </Text>
                </View>
                <Text
                  style={[
                    styles.stepDescription,
                    {
                      color: colors.textSecondary,
                      fontSize: 14,
                      fontFamily: typography.fontFamily.body,
                      marginLeft: 52, // Align with title (40px icon + 12px margin)
                    },
                  ]}
                >
                  {step.description}
                </Text>
              </View>
            ))}
          </View>
        </ScrollView>
      ) : (
        <>
          {/* Sort chips — hired tab only */}
          {activeTab === 'hired' && (
            <View
              style={[
                styles.sortBar,
                {
                  paddingHorizontal: spacing.screenPadding.horizontal,
                  paddingBottom: spacing.sm,
                },
              ]}
            >
              {SORT_OPTIONS.map((option) => (
                <TouchableOpacity
                  key={option.key}
                  testID={`sort-chip-${option.key}`}
                  onPress={() => setSortOption(option.key)}
                  style={[
                    styles.sortChip,
                    {
                      backgroundColor:
                        sortOption === option.key
                          ? colors.neonCyan + '30'
                          : colors.card,
                      borderColor:
                        sortOption === option.key
                          ? colors.neonCyan
                          : colors.textSecondary + '40',
                      borderWidth: 1,
                      borderRadius: spacing.md,
                      paddingHorizontal: spacing.md,
                      paddingVertical: spacing.xs,
                      marginRight: spacing.sm,
                    },
                  ]}
                >
                  <Text
                    style={{
                      color:
                        sortOption === option.key
                          ? colors.neonCyan
                          : colors.textSecondary,
                      fontSize: 13,
                      fontFamily: typography.fontFamily.body,
                    }}
                  >
                    {option.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          )}

          <FlatList
            data={agents}
            keyExtractor={(item: MyAgentInstanceSummary) => item.subscription_id}
            renderItem={({ item }: { item: MyAgentInstanceSummary }) => (
              <HiredAgentCard
                agent={item}
                onPress={() => handleAgentPress(item)}
              />
            )}
            contentContainerStyle={{
              paddingHorizontal: spacing.screenPadding.horizontal,
              paddingTop: 0,
              paddingBottom: spacing.xl,
            }}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={onRefresh}
                tintColor={colors.neonCyan}
                colors={[colors.neonCyan]}
              />
            }
          />
        </>
      )}

      {/* Voice Control */}
      <VoiceControl
        callbacks={{
          onNavigate: handleVoiceNavigate,
          onAction: handleVoiceAction,
          onHelp: handleVoiceHelp,
        }}
      />

      {/* Voice Help Modal */}
      <VoiceHelpModal
        visible={showVoiceHelp}
        onClose={() => setShowVoiceHelp(false)}
      />
    </SafeAreaView>
  );
};

/**
 * Hired Agent Card Component
 * Shows agent summary with status badge
 */
const HiredAgentCard = ({
  agent,
  onPress,
}: {
  agent: MyAgentInstanceSummary;
  onPress: () => void;
}) => {
  const { colors, spacing, typography } = useTheme();

  // Determine status badge
  const getStatusBadge = () => {
    if (agent.trial_status === 'active') {
      return { text: 'Trial Active', color: colors.success };
    }
    if (agent.trial_status === 'expired') {
      return { text: 'Trial Ended', color: colors.warning };
    }
    if (agent.cancel_at_period_end) {
      return { text: 'Ending Soon', color: colors.warning };
    }
    if (agent.status === 'active') {
      return { text: 'Active', color: colors.success };
    }
    return { text: agent.status, color: colors.textSecondary };
  };

  const badge = getStatusBadge();

  // Format trial dates
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <TouchableOpacity
      testID={`agent-card-${agent.subscription_id}`}
      style={[
        styles.agentCard,
        {
          backgroundColor: colors.card,
          borderRadius: spacing.md,
          padding: spacing.lg,
          marginBottom: spacing.md,
          borderWidth: 1,
          borderColor: colors.border,
        },
      ]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      {/* Header: Agent ID + Status Badge */}
      <View style={[styles.cardHeader, { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: spacing.sm }]}>
        <View style={{ flex: 1 }}>
          <Text
            testID={`agent-id-${agent.agent_id}`}
            style={[
              styles.agentId,
              {
                color: colors.textPrimary,
                fontSize: 16,
                fontFamily: typography.fontFamily.bodyBold,
                marginBottom: spacing.xs,
              },
            ]}
          >
            {agent.agent_id}
          </Text>
          {agent.nickname && (
            <Text
              style={[
                styles.nickname,
                {
                  color: colors.textSecondary,
                  fontSize: 14,
                  fontFamily: typography.fontFamily.body,
                },
              ]}
            >
              {agent.nickname}
            </Text>
          )}
        </View>

        <View
          style={[
            styles.statusBadge,
            {
              backgroundColor: badge.color + '20',
              borderRadius: spacing.sm,
              paddingHorizontal: spacing.md,
              paddingVertical: spacing.xs,
            },
          ]}
        >
          <Text
            style={[
              styles.statusText,
              {
                color: badge.color,
                fontSize: 12,
                fontFamily: typography.fontFamily.bodyBold,
              },
            ]}
          >
            {badge.text}
          </Text>
        </View>
      </View>

      {/* Trial Info */}
      {agent.trial_status === 'active' && agent.trial_start_at && agent.trial_end_at && (
        <View
          style={[
            styles.trialInfo,
            {
              backgroundColor: colors.neonCyan + '10',
              borderRadius: spacing.sm,
              padding: spacing.md,
              marginBottom: spacing.sm,
            },
          ]}
        >
          <Text
            style={[
              styles.trialLabel,
              {
                color: colors.neonCyan,
                fontSize: 12,
                fontFamily: typography.fontFamily.bodyBold,
                marginBottom: spacing.xs,
              },
            ]}
          >
            Trial Period
          </Text>
          <Text
            style={[
              styles.trialDates,
              {
                color: colors.textPrimary,
                fontSize: 14,
                fontFamily: typography.fontFamily.body,
              },
            ]}
          >
            {formatDate(agent.trial_start_at)} – {formatDate(agent.trial_end_at)}
          </Text>
        </View>
      )}

      {/* Subscription Info */}
      <View style={styles.subscriptionInfo}>
        <View style={[styles.infoRow, { flexDirection: 'row', justifyContent: 'space-between', marginBottom: spacing.xs }]}>
          <Text
            style={[
              styles.infoLabel,
              {
                color: colors.textSecondary,
                fontSize: 14,
                fontFamily: typography.fontFamily.body,
              },
            ]}
          >
            Duration
          </Text>
          <Text
            style={[
              styles.infoValue,
              {
                color: colors.textPrimary,
                fontSize: 14,
                fontFamily: typography.fontFamily.bodyBold,
              },
            ]}
          >
            {agent.duration.charAt(0).toUpperCase() + agent.duration.slice(1)}
          </Text>
        </View>
        <View style={[styles.infoRow, { flexDirection: 'row', justifyContent: 'space-between' }]}>
          <Text
            style={[
              styles.infoLabel,
              {
                color: colors.textSecondary,
                fontSize: 14,
                fontFamily: typography.fontFamily.body,
              },
            ]}
          >
            Next Billing
          </Text>
          <Text
            style={[
              styles.infoValue,
              {
                color: colors.textPrimary,
                fontSize: 14,
                fontFamily: typography.fontFamily.bodyBold,
              },
            ]}
          >
            {formatDate(agent.current_period_end)}
          </Text>
        </View>
      </View>

      {/* CTA hint */}
      <Text
        style={[
          styles.ctaHint,
          {
            color: colors.neonCyan,
            fontSize: 12,
            fontFamily: typography.fontFamily.body,
            marginTop: spacing.md,
            textAlign: 'right',
          },
        ]}
      >
        Tap to view {agent.trial_status === 'active' ? 'trial dashboard' : 'details'} →
      </Text>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
  },
  header: {},
  title: {},
  tabContainer: {},
  tab: {},
  tabText: {},
  scrollView: {
    flex: 1,
  },
  content: {
    paddingBottom: 40,
  },
  emptyState: {},
  emptyTitle: {},
  emptyText: {},
  ctaButton: {},
  ctaButtonText: {},
  infoSection: {},
  sectionTitle: {},
  stepCard: {},
  stepHeader: {},
  stepIcon: {},
  stepTitle: {},
  stepDescription: {},
  agentCard: {},
  cardHeader: {},
  agentId: {},
  nickname: {},
  statusBadge: {},
  statusText: {},
  trialInfo: {},
  trialLabel: {},
  trialDates: {},
  subscriptionInfo: {},
  infoRow: {},
  infoLabel: {},
  infoValue: {},
  ctaHint: {},
  sortBar: { flexDirection: 'row', flexWrap: 'wrap' },
  sortChip: {},
});
