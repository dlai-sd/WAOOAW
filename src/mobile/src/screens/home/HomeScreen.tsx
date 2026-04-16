/**
 * Home Screen (MOB-PARITY-2 E1-S1 + E1-S2)
 *
 * Single-screen no-scroll action dashboard. Shows 4 stat tiles
 * (agents active, trials live, pending approvals, billing alerts)
 * plus 2 action buttons — fits on screen without scrolling.
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  TouchableOpacity,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useTheme } from '../../hooks/useTheme';
import { useCurrentUser } from '../../store/authStore';
import { useHiredAgents } from '../../hooks/useHiredAgents';
import { useAllDeliverables } from '../../hooks/useAllDeliverables';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorView } from '../../components/ErrorView';

export const HomeScreen = () => {
  const { colors, spacing, typography } = useTheme();
  const user = useCurrentUser();
  const navigation = useNavigation<any>();

  const { data: hiredAgents, isLoading: agentsLoading, error: agentsError, refetch } = useHiredAgents();
  const { deliverables, isLoading: delivLoading } = useAllDeliverables();

  const isLoading = agentsLoading || delivLoading;
  const error = agentsError;

  const navigateToTab = React.useCallback(
    (tabName: 'DiscoverTab' | 'MyAgentsTab', screen: 'Discover' | 'MyAgents') => {
      navigation.getParent()?.navigate(tabName, { screen });
    },
    [navigation]
  );

  const handleApprovalsPress = React.useCallback(() => {
    navigation.getParent()?.navigate('MyAgentsTab', { screen: 'Inbox' });
  }, [navigation]);

  // Stat derivations
  const activeCount = (hiredAgents ?? []).filter((a) => a.subscription_status === 'active' || a.trial_status === 'active').length;
  const trialsLive = (hiredAgents ?? []).filter((a) => a.trial_status === 'active').length;
  const pendingCount = (deliverables ?? []).filter((d) => d.status === 'pending').length;
  const billingAlerts = (hiredAgents ?? []).filter((a) => a.subscription_status === 'past_due').length;

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 18) return 'Good Afternoon';
    return 'Good Evening';
  };

  if (isLoading) {
    return (
      <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.black }]}>
        <LoadingSpinner testID="home-loading" />
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.black }]}>
        <ErrorView message="Could not load your agents" onRetry={refetch} testID="home-error" />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.black }]}>
      <View
        style={[
          styles.container,
          {
            paddingHorizontal: spacing.screenPadding.horizontal,
            paddingVertical: spacing.screenPadding.vertical,
          },
        ]}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text
            style={{
              color: colors.textSecondary,
              fontSize: 14,
              fontFamily: typography.fontFamily.body,
            }}
          >
            {getGreeting()}
          </Text>
          <Text
            style={{
              color: colors.textPrimary,
              fontSize: 24,
              fontFamily: typography.fontFamily.display,
              marginTop: 2,
            }}
          >
            {user?.full_name || 'Welcome'}
          </Text>
        </View>

        {/* Stat tiles — 2×2 grid */}
        <View style={[styles.statsGrid, { marginTop: spacing.lg, gap: spacing.md }]}>
          {/* Agents Active */}
          <View
            testID="stat-agents-active"
            style={[styles.statTile, { backgroundColor: colors.card, borderRadius: spacing.md, padding: spacing.lg, flex: 1 }]}
          >
            <Text style={{ color: colors.neonCyan, fontSize: 28, fontFamily: typography.fontFamily.display }}>
              {activeCount}
            </Text>
            <Text style={{ color: colors.textSecondary, fontSize: 12, fontFamily: typography.fontFamily.body, marginTop: 4 }}>
              Agents active
            </Text>
          </View>

          {/* Trials Live */}
          <View
            testID="stat-trials-live"
            style={[styles.statTile, { backgroundColor: colors.card, borderRadius: spacing.md, padding: spacing.lg, flex: 1 }]}
          >
            <Text style={{ color: colors.neonCyan, fontSize: 28, fontFamily: typography.fontFamily.display }}>
              {trialsLive}
            </Text>
            <Text style={{ color: colors.textSecondary, fontSize: 12, fontFamily: typography.fontFamily.body, marginTop: 4 }}>
              Trials live
            </Text>
          </View>

          {/* Pending Approvals — tappable, navigates to Inbox */}
          <TouchableOpacity
            testID="stat-pending-approvals"
            onPress={handleApprovalsPress}
            style={[styles.statTile, { backgroundColor: colors.card, borderRadius: spacing.md, padding: spacing.lg, flex: 1 }]}
          >
            <Text
              style={{
                color: pendingCount > 0 ? (colors as unknown as Record<string, string>).warning ?? '#f59e0b' : colors.textSecondary,
                fontSize: 28,
                fontFamily: typography.fontFamily.display,
              }}
            >
              {pendingCount}
            </Text>
            <Text style={{ color: colors.textSecondary, fontSize: 12, fontFamily: typography.fontFamily.body, marginTop: 4 }}>
              Pending approvals
            </Text>
          </TouchableOpacity>

          {/* Billing Alerts */}
          <View
            testID="stat-billing-alerts"
            style={[styles.statTile, { backgroundColor: colors.card, borderRadius: spacing.md, padding: spacing.lg, flex: 1 }]}
          >
            <Text
              style={{
                color: billingAlerts > 0 ? colors.error : colors.textSecondary,
                fontSize: 28,
                fontFamily: typography.fontFamily.display,
              }}
            >
              {billingAlerts}
            </Text>
            <Text style={{ color: colors.textSecondary, fontSize: 12, fontFamily: typography.fontFamily.body, marginTop: 4 }}>
              Billing alerts
            </Text>
          </View>
        </View>

        {/* Action buttons */}
        <View style={[styles.actionsRow, { marginTop: spacing.xl, gap: spacing.md }]}>
          <TouchableOpacity
            testID="action-browse-agents"
            onPress={() => navigateToTab('DiscoverTab', 'Discover')}
            style={[
              styles.actionBtn,
              {
                backgroundColor: colors.neonCyan + '18',
                borderWidth: 1,
                borderColor: colors.neonCyan + '60',
                borderRadius: spacing.md,
                padding: spacing.lg,
                flex: 1,
                alignItems: 'center',
              },
            ]}
          >
            <Text style={{ fontSize: 24, marginBottom: 6 }}>🔍</Text>
            <Text style={{ color: colors.neonCyan, fontSize: 14, fontFamily: typography.fontFamily.bodyBold }}>
              Browse Agents
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            testID="action-my-agents"
            onPress={() => navigateToTab('MyAgentsTab', 'MyAgents')}
            style={[
              styles.actionBtn,
              {
                backgroundColor: colors.card,
                borderWidth: 1,
                borderColor: colors.textSecondary + '30',
                borderRadius: spacing.md,
                padding: spacing.lg,
                flex: 1,
                alignItems: 'center',
              },
            ]}
          >
            <Text style={{ fontSize: 24, marginBottom: 6 }}>🚀</Text>
            <Text style={{ color: colors.textPrimary, fontSize: 14, fontFamily: typography.fontFamily.bodyBold }}>
              My Agents
            </Text>
          </TouchableOpacity>
        </View>

        {/* Greeting subtitle */}
        <Text
          style={{
            color: colors.textSecondary,
            fontSize: 12,
            fontFamily: typography.fontFamily.body,
            textAlign: 'center',
            marginTop: spacing.xl,
          }}
        >
          WAOOAW · Agents Earn Your Business
        </Text>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
  },
  container: {
    flex: 1,
  },
  header: {},
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  statTile: {},
  actionsRow: {
    flexDirection: 'row',
  },
  actionBtn: {},
});
