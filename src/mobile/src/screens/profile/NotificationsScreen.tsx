/**
 * Notifications Screen (MOBILE-FUNC-1 S5)
 *
 * Push notification preferences — UI-only placeholder.
 * FCM token registration is wired in S8b (Iteration 3).
 *
 * CP-MOULD-1 E6-S1: Added agent-aware notification deep-links.
 * Tapping an agent notification navigates to AgentOperationsScreen
 * with the relevant focusSection pre-selected.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  SafeAreaView,
  ScrollView,
  Switch,
  TouchableOpacity,
} from 'react-native';
import { useTheme } from '@/hooks/useTheme';
import { registerPushToken } from '../../services/notifications/pushNotifications.service';
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

export const NotificationsScreen = ({ navigation }: Props) => {
  const { colors, spacing, typography } = useTheme();
  const parentNavigation = navigation.getParent() as any;
  const [pushEnabled, setPushEnabled] = useState(false);
  const [trialUpdates, setTrialUpdates] = useState(true);
  const [deliverableAlerts, setDeliverableAlerts] = useState(true);
  const [marketingEmails, setMarketingEmails] = useState(false);
  const actionableNotifications: Notification[] = [
    {
      id: 'demo-approval',
      type: 'approval_required',
      title: 'Approval waiting',
      body: 'A deliverable needs your sign-off before publication can continue.',
      hired_instance_id: 'demo-hired-agent-1',
      created_at: 'Just now',
    },
    {
      id: 'demo-approved',
      type: 'deliverable_approved',
      title: 'Deliverable approved and queued to publish',
      body: 'Your approved draft is moving into the runtime stream so you can verify the publication outcome.',
      hired_instance_id: 'demo-hired-agent-1',
      created_at: '42m ago',
    },
    {
      id: 'demo-publish-ready',
      type: 'publish_ready',
      title: 'YouTube upload is ready to proceed',
      body: 'Approval and channel readiness are satisfied, so you can confirm the latest publishing state from runtime progress.',
      hired_instance_id: 'demo-hired-agent-1',
      created_at: '1h ago',
    },
    {
      id: 'demo-publish-blocked',
      type: 'publish_blocked',
      title: 'YouTube publish blocked by connection state',
      body: 'The agent is approved to continue, but the connected YouTube channel still needs attention before upload can happen.',
      hired_instance_id: 'demo-hired-agent-1',
      created_at: '90m ago',
    },
    {
      id: 'demo-rejected',
      type: 'deliverable_rejected',
      title: 'Revision requested on a deliverable',
      body: 'A deliverable was not approved. Open activity to see what changed before the next revision arrives.',
      hired_instance_id: 'demo-hired-agent-2',
      created_at: '2h ago',
    },
  ];

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
        {actionableNotifications.map((notification) => (
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

