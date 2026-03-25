/**
 * Home Screen (MOBILE-COMP-1 E2-S2)
 *
 * Live mobile cockpit: derives priority pills and action items
 * from useHiredAgents data. Replaces static pills and setTimeout refresh.
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
  ActivityIndicator,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useTheme } from '../../hooks/useTheme';
import { useCurrentUser } from '../../store/authStore';
import { useHiredAgents } from '../../hooks/useHiredAgents';

export const HomeScreen = () => {
  const { colors, spacing, typography } = useTheme();
  const user = useCurrentUser();
  const navigation = useNavigation<any>();

  const { data: hiredAgents, isLoading, error, refetch, isFetching } = useHiredAgents();

  const navigateToTab = React.useCallback(
    (tabName: 'DiscoverTab' | 'MyAgentsTab', screen: 'Discover' | 'MyAgents') => {
      navigation.getParent()?.navigate(tabName, { screen });
    },
    [navigation]
  );

  const onRefresh = React.useCallback(() => {
    refetch();
  }, [refetch]);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 18) return 'Good Afternoon';
    return 'Good Evening';
  };

  // Derive live summary counts from hired agents
  const totalHires = hiredAgents?.length ?? 0;
  const activeTrials = hiredAgents?.filter((a) => a.trial_status === 'active').length ?? 0;
  const needsSetup = hiredAgents?.filter((a) => a.configured === false || a.goals_completed === false).length ?? 0;
  const pastDue = hiredAgents?.filter((a) => a.subscription_status === 'past_due').length ?? 0;

  // Derive live priority pills
  const livePills: string[] = [];
  if (needsSetup > 0) livePills.push(`${needsSetup} setup needed`);
  if (activeTrials > 0) livePills.push(`${activeTrials} trial${activeTrials > 1 ? 's' : ''} live`);
  if (pastDue > 0) livePills.push(`${pastDue} billing action`);
  if (livePills.length === 0 && totalHires > 0) livePills.push(`${totalHires} hire${totalHires > 1 ? 's' : ''} active`);

  // Derive live priorities
  const livePriorities: string[] = [];
  if (needsSetup > 0) {
    livePriorities.push('Complete agent setup so your hires can start working.');
  }
  if (pastDue > 0) {
    livePriorities.push('Update your payment method — a subscription is past due.');
  }
  const trialEndingSoon = hiredAgents?.filter((a) => {
    if (a.trial_status !== 'active' || !a.trial_end_at) return false;
    const msLeft = new Date(a.trial_end_at).getTime() - Date.now();
    return msLeft > 0 && msLeft <= 3 * 24 * 60 * 60 * 1000;
  }) ?? [];
  if (trialEndingSoon.length > 0) {
    livePriorities.push('A trial is ending in 3 days — review spend before it closes.');
  }

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.black }]}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={[
          styles.container,
          {
            paddingHorizontal: spacing.screenPadding.horizontal,
            paddingVertical: spacing.screenPadding.vertical,
          },
        ]}
        refreshControl={
          <RefreshControl
            refreshing={isFetching}
            onRefresh={onRefresh}
            tintColor={colors.neonCyan}
            colors={[colors.neonCyan]}
          />
        }
      >
        {/* Header */}
        <View style={[styles.header, { marginBottom: spacing.xl }]}>
          <Text
            style={[
              styles.greeting,
              {
                color: colors.textSecondary,
                fontSize: 16,
                fontFamily: typography.fontFamily.body,
                marginBottom: spacing.xs,
              },
            ]}
          >
            {getGreeting()}
          </Text>
          <Text
            style={[
              styles.userName,
              {
                color: colors.textPrimary,
                fontSize: 28,
                fontFamily: typography.fontFamily.display,
              },
            ]}
          >
            {user?.full_name || 'Welcome'}
          </Text>
        </View>

        {/* Hero Banner */}
        <View
          style={[
            styles.heroBanner,
            {
              backgroundColor: colors.neonCyan + '15',
              borderWidth: 1,
              borderColor: colors.neonCyan + '40',
              borderRadius: spacing.md,
              padding: spacing.lg,
              marginBottom: spacing.xl,
            },
          ]}
        >
          <Text
            style={[
              styles.heroTitle,
              {
                color: colors.neonCyan,
                fontSize: 32,
                fontFamily: typography.fontFamily.display,
                marginBottom: spacing.sm,
              },
            ]}
          >
            WAOOAW
          </Text>
          <Text
            style={[
              styles.heroSubtitle,
              {
                color: colors.textPrimary,
                fontSize: 18,
                fontFamily: typography.fontFamily.bodyBold,
                marginBottom: spacing.xs,
              },
            ]}
          >
            Agents Earn Your Business
          </Text>
          <Text
            style={[
              styles.heroDescription,
              {
                color: colors.textSecondary,
                fontSize: 14,
                fontFamily: typography.fontFamily.body,
              },
            ]}
          >
            Use mobile as your decision cockpit: what needs approval, what is running well, and where you should act next.
          </Text>

          {isLoading ? (
            <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: spacing.md }} testID="mobile-home-pills-loading">
              <ActivityIndicator size="small" color={colors.neonCyan} />
              <Text style={{ color: colors.textSecondary, fontSize: 12, fontFamily: typography.fontFamily.body, marginLeft: spacing.sm }}>
                Loading your agent status…
              </Text>
            </View>
          ) : error ? null : livePills.length > 0 ? (
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginTop: spacing.md }} testID="mobile-home-pills">
              {livePills.map((pill) => (
                <View
                  key={pill}
                  style={{
                    paddingHorizontal: spacing.md,
                    paddingVertical: spacing.xs,
                    borderRadius: 999,
                    borderWidth: 1,
                    borderColor: colors.neonCyan + '40',
                    backgroundColor: colors.black + '20',
                  }}
                >
                  <Text style={{ color: colors.textPrimary, fontSize: 12, fontFamily: typography.fontFamily.bodyBold }}>{pill}</Text>
                </View>
              ))}
            </View>
          ) : null}
        </View>

        <View style={[styles.section, { marginBottom: spacing.xl }]}> 
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
            Today&apos;s priorities
          </Text>
          {isLoading ? (
            <View style={{ padding: spacing.lg, alignItems: 'center' }} testID="mobile-home-priorities-loading">
              <ActivityIndicator color={colors.neonCyan} />
            </View>
          ) : error ? (
            <View style={{ padding: spacing.lg }} testID="mobile-home-priorities-error">
              <Text style={{ color: colors.textSecondary, fontFamily: typography.fontFamily.body, fontSize: 13 }}>
                Could not load priorities. Pull to refresh.
              </Text>
            </View>
          ) : livePriorities.length > 0 ? (
            <View style={{ gap: spacing.md }} testID="mobile-home-priorities">
              {livePriorities.map((item) => (
                <View
                  key={item}
                  style={{
                    backgroundColor: colors.card,
                    borderRadius: spacing.md,
                    padding: spacing.lg,
                    borderWidth: 1,
                    borderColor: colors.textSecondary + '20',
                  }}
                >
                  <Text style={{ color: colors.textPrimary, fontSize: 14, fontFamily: typography.fontFamily.body }}>{item}</Text>
                </View>
              ))}
            </View>
          ) : (
            <View style={{ padding: spacing.lg, alignItems: 'center' }} testID="mobile-home-priorities-empty">
              <Text style={{ color: colors.textSecondary, fontFamily: typography.fontFamily.body, fontSize: 14 }}>
                No action items right now. Discover agents or review your ops.
              </Text>
            </View>
          )}
        </View>

        {/* Quick Actions */}
        <View style={[styles.section, { marginBottom: spacing.xl }]}>
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
            Quick Actions
          </Text>
          <View style={[styles.quickActions, { gap: spacing.md }]}>
            <TouchableOpacity
              style={[
                styles.actionCard,
                {
                  backgroundColor: colors.card,
                  borderRadius: spacing.md,
                  padding: spacing.lg,
                  flex: 1,
                },
              ]}
              onPress={() => navigateToTab('DiscoverTab', 'Discover')}
            >
              <Text style={{ fontSize: 32, marginBottom: spacing.sm }}>🔍</Text>
              <Text
                style={[
                  styles.actionTitle,
                  {
                    color: colors.textPrimary,
                    fontSize: 16,
                    fontFamily: typography.fontFamily.bodyBold,
                  },
                ]}
              >
                Discover Agents
              </Text>
              <Text
                style={[
                  styles.actionDescription,
                  {
                    color: colors.textSecondary,
                    fontSize: 12,
                    fontFamily: typography.fontFamily.body,
                  },
                ]}
              >
                Browse 19+ AI agents
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.actionCard,
                {
                  backgroundColor: colors.card,
                  borderRadius: spacing.md,
                  padding: spacing.lg,
                  flex: 1,
                },
              ]}
              onPress={() => navigateToTab('MyAgentsTab', 'MyAgents')}
            >
              <Text style={{ fontSize: 32, marginBottom: spacing.sm }}>🚀</Text>
              <Text
                style={[
                  styles.actionTitle,
                  {
                    color: colors.textPrimary,
                    fontSize: 16,
                    fontFamily: typography.fontFamily.bodyBold,
                  },
                ]}
              >
                Open Ops
              </Text>
              <Text
                style={[
                  styles.actionDescription,
                  {
                    color: colors.textSecondary,
                    fontSize: 12,
                    fontFamily: typography.fontFamily.body,
                  },
                ]}
              >
                Review trials and hired agents
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Stats Section */}
        <View style={[styles.section, { marginBottom: spacing.xl }]}>
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
            Your Activity
          </Text>
          <View style={[styles.statsRow, { gap: spacing.md }]}>
            <View
              style={[
                styles.statCard,
                {
                  backgroundColor: colors.card,
                  borderRadius: spacing.md,
                  padding: spacing.lg,
                  flex: 1,
                  alignItems: 'center',
                },
              ]}
            >
              <Text
                style={[
                  styles.statValue,
                  {
                    color: colors.neonCyan,
                    fontSize: 32,
                    fontFamily: typography.fontFamily.display,
                    marginBottom: spacing.xs,
                  },
                ]}
              >
                {isLoading ? '…' : String(totalHires)}
              </Text>
              <Text
                style={[
                  styles.statLabel,
                  {
                    color: colors.textSecondary,
                    fontSize: 14,
                    fontFamily: typography.fontFamily.body,
                  },
                ]}
              >
                Active hires
              </Text>
            </View>

            <View
              style={[
                styles.statCard,
                {
                  backgroundColor: colors.card,
                  borderRadius: spacing.md,
                  padding: spacing.lg,
                  flex: 1,
                  alignItems: 'center',
                },
              ]}
            >
              <Text
                style={[
                  styles.statValue,
                  {
                    color: colors.neonCyan,
                    fontSize: 32,
                    fontFamily: typography.fontFamily.display,
                    marginBottom: spacing.xs,
                  },
                ]}
              >
                {isLoading ? '…' : String(activeTrials)}
              </Text>
              <Text
                style={[
                  styles.statLabel,
                  {
                    color: colors.textSecondary,
                    fontSize: 14,
                    fontFamily: typography.fontFamily.body,
                  },
                ]}
              >
                Trials live
              </Text>
            </View>
          </View>
        </View>

        {/* Discover CTA if no hires */}
        {!isLoading && !error && totalHires === 0 && (
          <View style={styles.section}>
            <View
              style={[
                styles.placeholderCard,
                {
                  backgroundColor: colors.card,
                  borderRadius: spacing.md,
                  padding: spacing.xl,
                  alignItems: 'center',
                },
              ]}
            >
              <Text style={{ fontSize: 48, marginBottom: spacing.md }}>🤖</Text>
              <Text
                style={[
                  styles.placeholderText,
                  {
                    color: colors.textSecondary,
                    fontSize: 14,
                    fontFamily: typography.fontFamily.body,
                    textAlign: 'center',
                  },
                ]}
              >
                No active hires yet
              </Text>
              <TouchableOpacity onPress={() => navigateToTab('DiscoverTab', 'Discover')} style={{ marginTop: spacing.md }}>
                <Text style={{ color: colors.neonCyan, fontFamily: typography.fontFamily.bodyBold, fontSize: 14 }}>
                  Browse agents →
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
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
    paddingBottom: 40,
  },
  header: {},
  greeting: {},
  userName: {},
  heroBanner: {},
  heroTitle: {},
  heroSubtitle: {},
  heroDescription: {},
  section: {},
  sectionTitle: {},
  quickActions: {
    flexDirection: 'row',
  },
  actionCard: {},
  actionTitle: {},
  actionDescription: {
    marginTop: 4,
  },
  statsRow: {
    flexDirection: 'row',
  },
  statCard: {},
  statValue: {},
  statLabel: {},
  placeholderCard: {},
  placeholderText: {},
  placeholderSubtext: {},
});
