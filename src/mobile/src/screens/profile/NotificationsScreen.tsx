/**
 * Notifications Screen (MOBILE-FUNC-1 S5)
 *
 * Push notification preferences — UI-only placeholder.
 * FCM token registration is wired in S8b (Iteration 3).
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
import type { ProfileStackScreenProps } from '@/navigation/types';

type Props = ProfileStackScreenProps<'Notifications'>;

export const NotificationsScreen = ({ navigation }: Props) => {
  const { colors, spacing, typography } = useTheme();
  const [pushEnabled, setPushEnabled] = useState(false);
  const [trialUpdates, setTrialUpdates] = useState(true);
  const [deliverableAlerts, setDeliverableAlerts] = useState(true);
  const [marketingEmails, setMarketingEmails] = useState(false);

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
            onValueChange={setPushEnabled}
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
