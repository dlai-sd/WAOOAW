/**
 * My Agents Screen
 * 
 * Shows active trials and hired agents
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
import { useTheme } from '../../hooks/useTheme';

export const MyAgentsScreen = () => {
  const { colors, spacing, typography } = useTheme();
  const [refreshing, setRefreshing] = React.useState(false);
  const [activeTab, setActiveTab] = React.useState<'trials' | 'hired'>('trials');

  const onRefresh = React.useCallback(() => {
    setRefreshing(true);
    // TODO: Fetch agents from API
    setTimeout(() => setRefreshing(false), 1000);
  }, []);

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.black }]}>
      <View style={[styles.header, { padding: spacing.screenPadding }]}>
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
              Active Trials (0)
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
              Hired (0)
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={[
          styles.content,
          { padding: spacing.screenPadding, paddingTop: 0 },
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
            {activeTab === 'trials' ? '⏳' : '🤝'}
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
              : 'No Hired Agents Yet'}
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
              : 'Hire agents after successful trials or direct from discovery'}
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
              Discover Agents
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

          <View
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
                  styles.stepNumber,
                  {
                    backgroundColor: colors.neonCyan + '30',
                    width: 32,
                    height: 32,
                    borderRadius: 16,
                    justifyContent: 'center',
                    alignItems: 'center',
                    marginRight: spacing.md,
                  },
                ]}
              >
                <Text
                  style={{
                    color: colors.neonCyan,
                    fontSize: 16,
                    fontFamily: typography.fontFamily.bodyBold,
                  }}
                >
                  1
                </Text>
              </View>
              <Text
                style={[
                  styles.stepTitle,
                  {
                    color: colors.textPrimary,
                    fontSize: 16,
                    fontFamily: typography.fontFamily.bodyBold,
                  },
                ]}
              >
                Start a 7-Day Trial
              </Text>
            </View>
            <Text
              style={[
                styles.stepDescription,
                {
                  color: colors.textSecondary,
                  fontSize: 14,
                  fontFamily: typography.fontFamily.body,
                },
              ]}
            >
              Try any agent risk-free. See real results on your business.
            </Text>
          </View>

          <View
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
                  styles.stepNumber,
                  {
                    backgroundColor: colors.neonCyan + '30',
                    width: 32,
                    height: 32,
                    borderRadius: 16,
                    justifyContent: 'center',
                    alignItems: 'center',
                    marginRight: spacing.md,
                  },
                ]}
              >
                <Text
                  style={{
                    color: colors.neonCyan,
                    fontSize: 16,
                    fontFamily: typography.fontFamily.bodyBold,
                  }}
                >
                  2
                </Text>
              </View>
              <Text
                style={[
                  styles.stepTitle,
                  {
                    color: colors.textPrimary,
                    fontSize: 16,
                    fontFamily: typography.fontFamily.bodyBold,
                  },
                ]}
              >
                Keep All Deliverables
              </Text>
            </View>
            <Text
              style={[
                styles.stepDescription,
                {
                  color: colors.textSecondary,
                  fontSize: 14,
                  fontFamily: typography.fontFamily.body,
                },
              ]}
            >
              Even if you don't hire, you keep everything the agent creates.
            </Text>
          </View>

          <View
            style={[
              styles.stepCard,
              {
                backgroundColor: colors.card,
                borderRadius: spacing.md,
                padding: spacing.lg,
              },
            ]}
          >
            <View style={[styles.stepHeader, { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.sm }]}>
              <View
                style={[
                  styles.stepNumber,
                  {
                    backgroundColor: colors.neonCyan + '30',
                    width: 32,
                    height: 32,
                    borderRadius: 16,
                    justifyContent: 'center',
                    alignItems: 'center',
                    marginRight: spacing.md,
                  },
                ]}
              >
                <Text
                  style={{
                    color: colors.neonCyan,
                    fontSize: 16,
                    fontFamily: typography.fontFamily.bodyBold,
                  }}
                >
                  3
                </Text>
              </View>
              <Text
                style={[
                  styles.stepTitle,
                  {
                    color: colors.textPrimary,
                    fontSize: 16,
                    fontFamily: typography.fontFamily.bodyBold,
                  },
                ]}
              >
                Hire What Works
              </Text>
            </View>
            <Text
              style={[
                styles.stepDescription,
                {
                  color: colors.textSecondary,
                  fontSize: 14,
                  fontFamily: typography.fontFamily.body,
                },
              ]}
            >
              Only pay for agents that deliver value. No surprises.
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
  stepNumber: {},
  stepTitle: {},
  stepDescription: {},
});
