/**
 * Home Screen
 * 
 * Main landing screen after authentication
 * Shows welcome message, featured agents, and quick actions
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
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useTheme } from '../../hooks/useTheme';
import { useCurrentUser } from '../../store/authStore';

export const HomeScreen = () => {
  const { colors, spacing, typography } = useTheme();
  const user = useCurrentUser();
  const navigation = useNavigation<any>();
  const [refreshing, setRefreshing] = React.useState(false);

  const navigateToTab = React.useCallback(
    (tabName: 'DiscoverTab' | 'MyAgentsTab', screen: 'Discover' | 'MyAgents') => {
      navigation.getParent()?.navigate(tabName, { screen });
    },
    [navigation]
  );

  const onRefresh = React.useCallback(() => {
    setRefreshing(true);
    // TODO: Fetch data from API
    setTimeout(() => setRefreshing(false), 1000);
  }, []);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 18) return 'Good Afternoon';
    return 'Good Evening';
  };

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
            refreshing={refreshing}
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

          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginTop: spacing.md }}>
            {['1 approval waiting', '2 hires live', 'Spend in control'].map((pill) => (
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
          <View style={{ gap: spacing.md }}>
            {[
              'Approve queued work before your agent misses a publish window.',
              'Review spend and receipts if a billing cycle is closing this week.',
              'Open My Agents to tune one more goal for your highest-value hire.',
            ].map((item) => (
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
                1
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
                Approvals waiting
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
                ₹6.4K
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
                Spend this week
              </Text>
            </View>
          </View>
        </View>

        {/* Featured Agents Placeholder */}
        <View style={styles.section}>
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
            Featured Agents
          </Text>
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
              Featured agents will appear here
            </Text>
            <Text
              style={[
                styles.placeholderSubtext,
                {
                  color: colors.textSecondary + '80',
                  fontSize: 12,
                  fontFamily: typography.fontFamily.body,
                  textAlign: 'center',
                  marginTop: spacing.xs,
                },
              ]}
            >
              Coming in Story 2.2
            </Text>
          </View>
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
