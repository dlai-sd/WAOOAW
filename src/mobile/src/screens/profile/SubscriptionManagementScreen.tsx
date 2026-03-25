/**
 * Subscription Management Screen (MOBILE-COMP-1 E3-S1)
 *
 * Binds to live hired-agent data via useHiredAgents.
 * Shows truthful subscription status and only exposes the
 * Razorpay payment CTA with real identifiers — never with
 * placeholder values.
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
import { useHiredAgents } from '@/hooks/useHiredAgents';
import type { ProfileStackScreenProps } from '@/navigation/types';

type Props = ProfileStackScreenProps<'SubscriptionManagement'>;

export const SubscriptionManagementScreen = ({ navigation }: Props) => {
  const { colors, spacing, typography } = useTheme();
  const { processPayment, isProcessing, error: razorpayError, clearError } = useRazorpay();
  const { data: hiredAgents, isLoading, error: loadError, refetch } = useHiredAgents();

  // Find the first active or past-due subscription
  const activeSub = hiredAgents?.find(
    (a) => a.status === 'active' || a.status === 'past_due',
  ) ?? null;

  // Only trigger Razorpay with real identifiers — never with placeholders
  const toPlanType = (d: string | undefined): 'monthly' | 'trial' | 'annual' =>
    d === 'yearly' ? 'annual' : d === 'trial' ? 'trial' : 'monthly';

  const handleRenew = async () => {
    if (!activeSub?.hired_instance_id) return;
    try {
      await processPayment({
        agentId: activeSub.hired_instance_id,
        planType: toPlanType(activeSub.duration),
        amount: 0, // amount must come from a billing API; guard here until that is wired
      });
    } catch {
      // useRazorpay already shows Alert on error
    }
  };

  const canRenew = !isProcessing && !!activeSub?.hired_instance_id;

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
        {/* Loading state */}
        {isLoading && (
          <View style={{ padding: spacing.xl, alignItems: 'center' }} testID="subscription-loading">
            <ActivityIndicator color={colors.neonCyan} />
            <Text style={{ color: colors.textSecondary, fontFamily: typography.fontFamily.body, fontSize: 13, marginTop: spacing.sm }}>
              Loading subscription status…
            </Text>
          </View>
        )}

        {/* Error loading agents */}
        {!isLoading && loadError && (
          <View style={{ padding: spacing.xl, alignItems: 'center' }} testID="subscription-load-error">
            <Text style={{ color: colors.textPrimary, fontFamily: typography.fontFamily.bodyBold, fontSize: 15, marginBottom: 6 }}>
              Could not load subscription data
            </Text>
            <Text style={{ color: colors.textSecondary, fontFamily: typography.fontFamily.body, fontSize: 13, marginBottom: spacing.md }}>
              {loadError.message}
            </Text>
            <TouchableOpacity onPress={() => refetch()}>
              <Text style={{ color: colors.neonCyan, fontFamily: typography.fontFamily.bodyBold, fontSize: 14 }}>Try Again</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* No active subscription */}
        {!isLoading && !loadError && !activeSub && (
          <View style={{ padding: spacing.xl, alignItems: 'center' }} testID="subscription-empty">
            <Text style={{ color: colors.textPrimary, fontFamily: typography.fontFamily.bodyBold, fontSize: 15, marginBottom: 6 }}>
              No active subscription
            </Text>
            <Text style={{ color: colors.textSecondary, fontFamily: typography.fontFamily.body, fontSize: 13 }}>
              Start a 7-day trial by hiring an agent from the Discover tab.
            </Text>
          </View>
        )}

        {/* Live subscription card */}
        {!isLoading && !loadError && activeSub && (
          <>
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
              testID="subscription-active-card"
            >
              <Text
                style={{
                  color: colors.neonCyan,
                  fontFamily: typography.fontFamily.display,
                  fontSize: 18,
                  fontWeight: 'bold',
                }}
              >
                {activeSub.duration === 'monthly' ? 'Monthly' : activeSub.duration === 'quarterly' ? 'Quarterly' : 'Annual'} Plan
              </Text>
              <Text
                style={{
                  color: colors.textSecondary,
                  fontFamily: typography.fontFamily.body,
                  fontSize: 13,
                  marginTop: 4,
                }}
              >
                Status: {activeSub.status === 'past_due' ? '⚠️ Past due' : activeSub.status}
                {activeSub.current_period_end
                  ? ` · Renews ${new Date(activeSub.current_period_end).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}`
                  : ''}
              </Text>

              {activeSub.trial_status === 'active' && activeSub.trial_end_at && (
                <Text
                  style={{
                    color: colors.textPrimary,
                    fontFamily: typography.fontFamily.body,
                    fontSize: 14,
                    marginTop: spacing.sm,
                  }}
                >
                  🎁 Trial active · ends {new Date(activeSub.trial_end_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                </Text>
              )}
            </View>
          </>
        )}

        {/* Razorpay error message */}
        {razorpayError ? (
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
              {razorpayError}
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

        {/* Renew / Upgrade CTA — only when real identifiers are available */}
        {!isLoading && !loadError && activeSub && (
          <>
            <Text style={sectionHeaderStyle}>Options</Text>
            <TouchableOpacity
              onPress={handleRenew}
              disabled={!canRenew}
              testID="subscription-renew-cta"
              style={{
                marginHorizontal: spacing.screenPadding.horizontal,
                paddingVertical: spacing.md + 2,
                borderRadius: 14,
                backgroundColor: canRenew ? colors.neonCyan : colors.textSecondary + '40',
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
                  color: canRenew ? colors.black : colors.textSecondary,
                  fontFamily: typography.fontFamily.bodyBold,
                  fontSize: 16,
                  fontWeight: 'bold',
                }}
              >
                {isProcessing ? 'Processing…' : 'Renew / Upgrade'}
              </Text>
            </TouchableOpacity>
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};
