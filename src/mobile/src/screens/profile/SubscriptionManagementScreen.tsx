/**
 * Subscription Management Screen (MOBILE-FUNC-1 S7)
 *
 * Shows the current subscription tier and a "Renew / Upgrade" CTA that
 * triggers the Razorpay payment flow using the existing useRazorpay hook.
 */

import React from 'react';
import {
  View,
  Text,
  SafeAreaView,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useTheme } from '@/hooks/useTheme';
import { useRazorpay } from '@/hooks/useRazorpay';
import type { ProfileStackScreenProps } from '@/navigation/types';

type Props = ProfileStackScreenProps<'SubscriptionManagement'>;

export const SubscriptionManagementScreen = ({ navigation }: Props) => {
  const { colors, spacing, typography } = useTheme();
  const { processPayment, isProcessing, error, clearError } = useRazorpay();

  // -------------------------------------------------------------------
  // Razorpay trigger pattern (MOBILE-FUNC-1 S7 code block)
  // -------------------------------------------------------------------
  const handleRenew = async () => {
    try {
      // agentId and planId should come from the user's current subscription;
      // using placeholder values until subscription query is wired in a future story.
      await processPayment({ agentId: 'current', planType: 'monthly', amount: 12000 });
    } catch {
      // useRazorpay already shows Alert on error — no double-handling needed
    }
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
      {/* Header */}
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
          Subscription
        </Text>
      </View>

      <ScrollView>
        {/* Current plan */}
        <Text style={sectionHeaderStyle}>Current Plan</Text>
        <View
          style={{
            marginHorizontal: spacing.screenPadding.horizontal,
            padding: spacing.lg,
            borderRadius: 16,
            borderWidth: 1,
            borderColor: colors.neonCyan + '60',
            backgroundColor: colors.neonCyan + '10',
          }}
        >
          <Text
            style={{
              color: colors.neonCyan,
              fontFamily: typography.fontFamily.display,
              fontSize: 18,
              fontWeight: 'bold',
            }}
          >
            Pro Monthly
          </Text>
          <Text
            style={{
              color: colors.textSecondary,
              fontFamily: typography.fontFamily.body,
              fontSize: 13,
              marginTop: 4,
            }}
          >
            ₹12,000 / month · Renews on 6 Apr 2026
          </Text>

          {/* Feature list */}
          {['Unlimited agent runs', '7-day trials', 'Priority support', 'Deliverable exports'].map(
            (feat) => (
              <Text
                key={feat}
                style={{
                  color: colors.textPrimary,
                  fontFamily: typography.fontFamily.body,
                  fontSize: 14,
                  marginTop: spacing.sm,
                }}
              >
                ✓ {feat}
              </Text>
            ),
          )}
        </View>

        {/* Error message */}
        {error ? (
          <View
            style={{
              marginHorizontal: spacing.screenPadding.horizontal,
              marginTop: spacing.md,
              padding: spacing.md,
              borderRadius: 8,
              backgroundColor: colors.error + '20',
            }}
          >
            <Text
              style={{
                color: colors.error,
                fontFamily: typography.fontFamily.body,
                fontSize: 13,
              }}
            >
              {error}
            </Text>
            <TouchableOpacity onPress={clearError} style={{ marginTop: 4 }}>
              <Text
                style={{
                  color: colors.textSecondary,
                  fontSize: 12,
                  textDecorationLine: 'underline',
                }}
              >
                Dismiss
              </Text>
            </TouchableOpacity>
          </View>
        ) : null}

        {/* Renew / Upgrade CTA */}
        <Text style={sectionHeaderStyle}>Options</Text>
        <TouchableOpacity
          onPress={handleRenew}
          disabled={isProcessing}
          style={{
            marginHorizontal: spacing.screenPadding.horizontal,
            paddingVertical: spacing.md + 2,
            borderRadius: 14,
            backgroundColor: colors.neonCyan,
            alignItems: 'center' as const,
            flexDirection: 'row' as const,
            justifyContent: 'center' as const,
            gap: 8,
          }}
        >
          {isProcessing ? (
            <ActivityIndicator color={colors.black} size="small" />
          ) : null}
          <Text
            style={{
              color: colors.black,
              fontFamily: typography.fontFamily.bodyBold,
              fontSize: 16,
              fontWeight: 'bold',
            }}
          >
            {isProcessing ? 'Processing…' : 'Renew / Upgrade'}
          </Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
};
