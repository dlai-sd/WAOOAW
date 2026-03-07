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
import type { ProfileStackScreenProps } from '@/navigation/types';
import { useNavigation } from '@react-navigation/native';

type Props = ProfileStackScreenProps<'Notifications'>;

// ─── Notification types & deep-link resolver ──────────────────────────────────

export type NotificationType =
  | 'approval_required'    // → AgentOperationsScreen, section: "approvals"
  | 'credential_expiring'  // → AgentOperationsScreen, section: "health"
  | 'agent_paused'         // → AgentOperationsScreen, section: "scheduler"
  | 'trial_ending'         // → AgentOperationsScreen, section: "spend"
  | 'goal_run_failed'      // → AgentOperationsScreen, section: "activity"
  | 'generic';             // → no navigation

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  body: string;
  hired_agent_id?: string;
  read?: boolean;
  created_at?: string;
}

/**
 * Resolves a notification to a navigation target.
 * Returns null for generic notifications or those without hired_agent_id.
 */
export function resolveNavigationTarget(
  notification: Notification
): { screen: string; params: object } | null {
  if (!notification.hired_agent_id) return null;
  switch (notification.type) {
    case 'approval_required':
      return {
        screen: 'AgentOperations',
        params: { hiredAgentId: notification.hired_agent_id, focusSection: 'approvals' },
      };
    case 'credential_expiring':
      return {
        screen: 'AgentOperations',
        params: { hiredAgentId: notification.hired_agent_id, focusSection: 'health' },
      };
    case 'agent_paused':
      return {
        screen: 'AgentOperations',
        params: { hiredAgentId: notification.hired_agent_id, focusSection: 'scheduler' },
      };
    case 'trial_ending':
      return {
        screen: 'AgentOperations',
        params: { hiredAgentId: notification.hired_agent_id, focusSection: 'spend' },
      };
    case 'goal_run_failed':
      return {
        screen: 'AgentOperations',
        params: { hiredAgentId: notification.hired_agent_id, focusSection: 'activity' },
      };
    default:
      return null;
  }
}

// ─── Screen ───────────────────────────────────────────────────────────────────

export const NotificationsScreen = ({ navigation }: Props) => {
  const { colors, spacing, typography } = useTheme();
  const rootNavigation = useNavigation<any>();
  const [pushEnabled, setPushEnabled] = useState(false);
  const [trialUpdates, setTrialUpdates] = useState(true);
  const [deliverableAlerts, setDeliverableAlerts] = useState(true);
  const [marketingEmails, setMarketingEmails] = useState(false);

  const handlePushToggle = (value: boolean) => {
    setPushEnabled(value);
    if (value) {
      registerPushToken().catch(() => {});
    }
  };

  const handleNotificationPress = (notification: Notification) => {
    const target = resolveNavigationTarget(notification);
    if (target) {
      rootNavigation.navigate('MyAgentsTab', {
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
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.black }}>
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

