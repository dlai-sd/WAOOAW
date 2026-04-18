/**
 * Notifications Screen (MOBILE-COMP-1 E2-S1)
 *
 * Derives a live actionable inbox from useHiredAgents data.
 * Replaces the previous hard-coded demo array with truthful
 * loading, empty, and error states.
 *
 * CP-MOULD-1 E6-S1: Agent-aware notification deep-links preserved.
 * Tapping an alert navigates to AgentOperationsScreen with the
 * relevant focusSection pre-selected.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  SafeAreaView,
  ScrollView,
  Switch,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useTheme } from '@/hooks/useTheme';
import { useHiredAgents } from '@/hooks/useHiredAgents';
import { registerPushToken } from '../../services/notifications/pushNotifications.service';
import type { MyAgentInstanceSummary } from '@/types/hiredAgents.types';
import type {
  AgentOperationsFocusSection,
  MyAgentsStackParamList,
  ProfileStackScreenProps,
} from '@/navigation/types';

type Props = ProfileStackScreenProps<'Notifications'>;

// ─── Notification types & deep-link resolver ──────────────────────────────────

export type NotificationType =
  | 'approval_required'    // → AgentOperationsScreen, section: "approvals"
  | 'deliverable_approved' // → AgentOperationsScreen, section: "recent"
  | 'deliverable_rejected' // → AgentOperationsScreen, section: "activity"
  | 'credential_expiring'  // → AgentOperationsScreen, section: "health"
  | 'agent_paused'         // → AgentOperationsScreen, section: "scheduler"
  | 'trial_ending'         // → AgentOperationsScreen, section: "spend"
  | 'goal_run_failed'      // → AgentOperationsScreen, section: "activity"
  | 'publish_ready'        // → AgentOperationsScreen, section: "recent"
  | 'publish_blocked'      // → AgentOperationsScreen, section: "health"
  | 'generic';             // → no navigation

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  body: string;
  hired_instance_id?: string;
  hired_agent_id?: string;
  read?: boolean;
  created_at?: string;
}

function getRuntimeId(notification: Notification): string | undefined {
  return notification.hired_instance_id || notification.hired_agent_id;
}

const FOCUS_SECTION_LABELS: Record<AgentOperationsFocusSection, string> = {
  activity: "today's activity",
  approvals: 'pending approvals',
  scheduler: 'schedule controls',
  health: 'connection health',
  goals: 'goal configuration',
  spend: 'trial usage and spend',
  recent: 'recent publications',
  history: 'performance history',
}

function getNotificationDestinationLabel(notification: Notification): string {
  const runtimeId = getRuntimeId(notification)
  const target = resolveNavigationTarget(notification)

  if (!runtimeId || !target) {
    return 'No runtime action is attached to this alert.'
  }

  const focusSection = (target.params as { focusSection?: string }).focusSection
  const destinationLabel = focusSection && focusSection in FOCUS_SECTION_LABELS
    ? FOCUS_SECTION_LABELS[focusSection as AgentOperationsFocusSection]
    : 'agent operations'

  return `Opens ${destinationLabel} for runtime ${runtimeId}.`
}

/**
 * Resolves a notification to a navigation target.
 * Returns null for generic notifications or those without hired_agent_id.
 */
export function resolveNavigationTarget(
  notification: Notification
): {
  screen: 'AgentOperations';
  params: MyAgentsStackParamList['AgentOperations'];
} | null {
  const runtimeId = getRuntimeId(notification)
  if (!runtimeId) return null;
  switch (notification.type) {
    case 'approval_required':
      return {
        screen: 'AgentOperations',
        params: { hiredAgentId: runtimeId, focusSection: 'approvals' },
      };
    case 'deliverable_approved':
      return {
        screen: 'AgentOperations',
        params: { hiredAgentId: runtimeId, focusSection: 'recent' },
      };
    case 'deliverable_rejected':
      return {
        screen: 'AgentOperations',
        params: { hiredAgentId: runtimeId, focusSection: 'activity' },
      };
    case 'publish_ready':
      return {
        screen: 'AgentOperations',
        params: { hiredAgentId: runtimeId, focusSection: 'recent' },
      };
    case 'publish_blocked':
      return {
        screen: 'AgentOperations',
        params: { hiredAgentId: runtimeId, focusSection: 'health' },
      };
    case 'credential_expiring':
      return {
        screen: 'AgentOperations',
        params: { hiredAgentId: runtimeId, focusSection: 'health' },
      };
    case 'agent_paused':
      return {
        screen: 'AgentOperations',
        params: { hiredAgentId: runtimeId, focusSection: 'scheduler' },
      };
    case 'trial_ending':
      return {
        screen: 'AgentOperations',
        params: { hiredAgentId: runtimeId, focusSection: 'spend' },
      };
    case 'goal_run_failed':
      return {
        screen: 'AgentOperations',
        params: { hiredAgentId: runtimeId, focusSection: 'activity' },
      };
    default:
      return null;
  }
}

// ─── Screen ───────────────────────────────────────────────────────────────────

/** Derive a truthful list of actionable notifications from live hired-agent data. */
export function deriveActionableNotifications(
  agents: MyAgentInstanceSummary[],
): Notification[] {
  const notifications: Notification[] = [];
  const now = Date.now();

  agents.forEach((agent) => {
    const runtimeId = agent.hired_instance_id ?? undefined;

    // Configuration incomplete
    if (agent.configured === false || agent.goals_completed === false) {
      notifications.push({
        id: `setup-${agent.hired_instance_id ?? agent.subscription_id}`,
        type: 'approval_required',
        title: 'Agent setup incomplete',
        body: 'Complete platform connection and goals so this agent can start working for you.',
        hired_instance_id: runtimeId,
        hired_agent_id: (agent.hired_instance_id ?? undefined) as string | undefined,
        created_at: agent.trial_start_at ?? undefined,
      });
    }

    // Trial ending within 3 days
    if (agent.trial_status === 'active' && agent.trial_end_at) {
      const msUntilEnd = new Date(agent.trial_end_at).getTime() - now;
      const threeDaysMs = 3 * 24 * 60 * 60 * 1000;
      if (msUntilEnd > 0 && msUntilEnd <= threeDaysMs) {
        notifications.push({
          id: `trial-ending-${agent.hired_instance_id ?? agent.subscription_id}`,
          type: 'trial_ending',
          title: 'Trial ending soon',
          body: 'Your trial is ending in less than 3 days. Review spend and decide whether to continue.',
          hired_instance_id: runtimeId,
          hired_agent_id: (agent.hired_instance_id ?? undefined) as string | undefined,
          created_at: agent.trial_end_at,
        });
      }
    }

    // Past-due subscription → credential/health warning
    if (agent.subscription_status === 'past_due') {
      notifications.push({
        id: `billing-${agent.subscription_id}`,
        type: 'credential_expiring',
        title: 'Billing action needed',
        body: 'Your subscription payment is past due. Update your payment method to keep this agent running.',
        hired_instance_id: runtimeId,
        hired_agent_id: (agent.hired_instance_id ?? undefined) as string | undefined,
        created_at: agent.current_period_end ?? undefined,
      });
    }
  });

  return notifications;
}

export const NotificationsScreen = ({ navigation }: Props) => {
  const { colors, spacing, typography } = useTheme();
  const parentNavigation = navigation.getParent() as any;
  const [pushEnabled, setPushEnabled] = useState(false);
  const [trialUpdates, setTrialUpdates] = useState(true);
  const [deliverableAlerts, setDeliverableAlerts] = useState(true);
  const [marketingEmails, setMarketingEmails] = useState(false);

  const { data: hiredAgents, isLoading, error, refetch } = useHiredAgents();
  const actionableNotifications: Notification[] = hiredAgents
    ? deriveActionableNotifications(hiredAgents)
    : [];

  const handlePushToggle = (value: boolean) => {
    setPushEnabled(value);
    if (value) {
      registerPushToken().catch(() => {});
    }
  };

  const handleNotificationPress = (notification: Notification) => {
    const target = resolveNavigationTarget(notification);
    if (target) {
      parentNavigation?.navigate('MyAgentsTab', {
        screen: target.screen,
        params: target.params,
      });
    }
  };

  const rowStyle = {
    flexDirection: 'row' as const,
    alignItems: 'center' as const,
    justifyContent: 'space-between' as const,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.screenPadding.horizontal,
    borderBottomWidth: 1,
    borderBottomColor: colors.border + '40',
  };

  const labelStyle = {
    color: colors.textPrimary,
    fontFamily: typography.fontFamily.body,
    fontSize: 16,
    flex: 1,
  };

  const sublabelStyle = {
    color: colors.textSecondary,
    fontFamily: typography.fontFamily.body,
    fontSize: 12,
    marginTop: 2,
  };

  const sectionHeaderStyle = {
    color: colors.textSecondary,
    fontFamily: typography.fontFamily.body,
    fontSize: 12,
    textTransform: 'uppercase' as const,
    letterSpacing: 1,
    paddingHorizontal: spacing.screenPadding.horizontal,
    paddingTop: spacing.lg,
    paddingBottom: spacing.sm,
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.black }} testID="mobile-notifications-screen">
      <View
        style={{
          paddingHorizontal: spacing.screenPadding.horizontal,
          paddingTop: spacing.md,
          paddingBottom: spacing.sm,
        }}
      >
        <TouchableOpacity
          onPress={() => navigation.goBack()}
          style={{ marginBottom: spacing.md }}
        >
          <Text
            style={{
              color: colors.neonCyan,
              fontFamily: typography.fontFamily.body,
              fontSize: 14,
            }}
          >
            ← Back
          </Text>
        </TouchableOpacity>
        <Text
          style={{
            color: colors.textPrimary,
            fontFamily: typography.fontFamily.display,
            fontSize: 24,
            fontWeight: 'bold',
          }}
        >
          Notifications
        </Text>
      </View>

      <ScrollView>
        {/* Push Notifications master toggle */}
        <Text style={sectionHeaderStyle}>Push Notifications</Text>
        <View style={rowStyle}>
          <View style={{ flex: 1 }}>
            <Text style={labelStyle}>Enable Push Notifications</Text>
            <Text style={sublabelStyle}>
              Receive alerts directly on your device
            </Text>
          </View>
          <Switch
            value={pushEnabled}
            onValueChange={handlePushToggle}
            trackColor={{ false: colors.border, true: colors.neonCyan }}
            thumbColor={pushEnabled ? colors.black : colors.textSecondary}
          />
        </View>

        <Text style={sectionHeaderStyle}>Action Routing</Text>
        <View
          style={{
            marginHorizontal: spacing.screenPadding.horizontal,
            marginBottom: spacing.sm,
            padding: spacing.md,
            borderRadius: 12,
            borderWidth: 1,
            borderColor: colors.border + '40',
            backgroundColor: colors.card,
          }}
        >
          <Text style={{ color: colors.textPrimary, fontFamily: typography.fontFamily.bodyBold, fontSize: 15, marginBottom: 6 }}>
            Approval and deliverable alerts should land you in the right Ops section.
          </Text>
          <Text style={{ color: colors.textSecondary, fontFamily: typography.fontFamily.body, fontSize: 13 }}>
            Tap an alert preview below to jump into the agent operations hub with the relevant section already opened for the event that just changed.
          </Text>
        </View>
        {isLoading && (
          <View style={{ padding: spacing.xl, alignItems: 'center' }} testID="mobile-notifications-loading">
            <ActivityIndicator color={colors.neonCyan} />
            <Text style={{ color: colors.textSecondary, fontFamily: typography.fontFamily.body, fontSize: 13, marginTop: spacing.sm }}>
              Loading your agent alerts…
            </Text>
          </View>
        )}
        {!isLoading && error && (
          <View style={{ padding: spacing.xl, alignItems: 'center' }} testID="mobile-notifications-error">
            <Text style={{ color: colors.textPrimary, fontFamily: typography.fontFamily.bodyBold, fontSize: 15, marginBottom: 6 }}>
              Could not load alerts
            </Text>
            <Text style={{ color: colors.textSecondary, fontFamily: typography.fontFamily.body, fontSize: 13, marginBottom: spacing.md }}>
              {error.message}
            </Text>
            <TouchableOpacity onPress={() => refetch()}>
              <Text style={{ color: colors.neonCyan, fontFamily: typography.fontFamily.bodyBold, fontSize: 14 }}>Try Again</Text>
            </TouchableOpacity>
          </View>
        )}
        {!isLoading && !error && actionableNotifications.length === 0 && (
          <View style={{ padding: spacing.xl, alignItems: 'center' }} testID="mobile-notifications-empty">
            <Text style={{ color: colors.textPrimary, fontFamily: typography.fontFamily.bodyBold, fontSize: 15, marginBottom: 6 }}>
              No action items right now
            </Text>
            <Text style={{ color: colors.textSecondary, fontFamily: typography.fontFamily.body, fontSize: 13 }}>
              When an agent needs attention or your trial status changes, alerts will appear here.
            </Text>
          </View>
        )}
        {!isLoading && !error && actionableNotifications.map((notification) => (
          <TouchableOpacity
            key={notification.id}
            style={{
              marginHorizontal: spacing.screenPadding.horizontal,
              marginBottom: spacing.sm,
              padding: spacing.md,
              borderRadius: 12,
              borderWidth: 1,
              borderColor: colors.border + '40',
              backgroundColor: colors.card,
            }}
            onPress={() => handleNotificationPress(notification)}
            testID={`mobile-notification-${notification.id}`}
          >
            <Text style={{ color: colors.textPrimary, fontFamily: typography.fontFamily.bodyBold, fontSize: 15, marginBottom: 4 }}>
              {notification.title}
            </Text>
            <Text style={{ color: colors.textSecondary, fontFamily: typography.fontFamily.body, fontSize: 13, marginBottom: 8 }}>
              {notification.body}
            </Text>
            <Text style={{ color: colors.neonCyan, fontFamily: typography.fontFamily.bodyBold, fontSize: 12 }}>
              {getNotificationDestinationLabel(notification)}
            </Text>
          </TouchableOpacity>
        ))}

        {/* Alert types */}
        <Text style={sectionHeaderStyle}>Alert Types</Text>
        <View style={{ ...rowStyle, opacity: pushEnabled ? 1 : 0.4 }}>
          <View style={{ flex: 1 }}>
            <Text style={labelStyle}>Trial Updates</Text>
            <Text style={sublabelStyle}>When your trial status changes</Text>
          </View>
          <Switch
            value={trialUpdates && pushEnabled}
            onValueChange={setTrialUpdates}
            disabled={!pushEnabled}
            trackColor={{ false: colors.border, true: colors.neonCyan }}
            thumbColor={trialUpdates ? colors.black : colors.textSecondary}
          />
        </View>
        <View style={{ ...rowStyle, opacity: pushEnabled ? 1 : 0.4 }}>
          <View style={{ flex: 1 }}>
            <Text style={labelStyle}>New Deliverables</Text>
            <Text style={sublabelStyle}>
              When an agent delivers new work
            </Text>
          </View>
          <Switch
            value={deliverableAlerts && pushEnabled}
            onValueChange={setDeliverableAlerts}
            disabled={!pushEnabled}
            trackColor={{ false: colors.border, true: colors.neonCyan }}
            thumbColor={deliverableAlerts ? colors.black : colors.textSecondary}
          />
        </View>

        {/* Email */}
        <Text style={sectionHeaderStyle}>Email</Text>
        <View style={rowStyle}>
          <View style={{ flex: 1 }}>
            <Text style={labelStyle}>Marketing Updates</Text>
            <Text style={sublabelStyle}>
              New agents, features and promotions
            </Text>
          </View>
          <Switch
            value={marketingEmails}
            onValueChange={setMarketingEmails}
            trackColor={{ false: colors.border, true: colors.neonCyan }}
            thumbColor={marketingEmails ? colors.black : colors.textSecondary}
          />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

