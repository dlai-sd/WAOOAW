/**
 * Payment Methods Screen (MOBILE-FUNC-1 S7)
 *
 * Shows stored payment methods with an "Add Payment Method" CTA
 * that triggers the Razorpay payment flow.
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

type Props = ProfileStackScreenProps<'PaymentMethods'>;

// Static placeholder payment methods — replace with real API query when available
const PLACEHOLDER_METHODS = [
  { id: 'pm_1', type: 'UPI', label: 'user@upi', icon: '💳' },
  { id: 'pm_2', type: 'Card', label: '**** **** **** 4242', icon: '🏦' },
];

export const PaymentMethodsScreen = ({ navigation }: Props) => {
  const { colors, spacing, typography } = useTheme();
  const { processPayment, isProcessing } = useRazorpay();

  const handleAddPaymentMethod = async () => {
    // Trigger a ₹1 verification payment to vault the new method
    await processPayment({
      agentId: 'verification',
      planType: 'trial',
      amount: 1,
    });
  };

  const rowStyle = {
    flexDirection: 'row' as const,
    alignItems: 'center' as const,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.screenPadding.horizontal,
    borderBottomWidth: 1,
    borderBottomColor: colors.border + '40',
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
          Payment Methods
        </Text>
      </View>

      <ScrollView>
        {/* Saved methods */}
        <Text style={sectionHeaderStyle}>Saved Methods</Text>
        {PLACEHOLDER_METHODS.map((method) => (
          <View key={method.id} style={rowStyle}>
            <Text style={{ fontSize: 22, marginRight: spacing.md }}>
              {method.icon}
            </Text>
            <View>
              <Text
                style={{
                  color: colors.textPrimary,
                  fontFamily: typography.fontFamily.body,
                  fontSize: 15,
                }}
              >
                {method.label}
              </Text>
              <Text
                style={{
                  color: colors.textSecondary,
                  fontFamily: typography.fontFamily.body,
                  fontSize: 12,
                  marginTop: 2,
                }}
              >
                {method.type}
              </Text>
            </View>
          </View>
        ))}

        {/* CTA */}
        <Text style={sectionHeaderStyle}>Add New</Text>
        <TouchableOpacity
          onPress={handleAddPaymentMethod}
          disabled={isProcessing}
          style={{
            marginHorizontal: spacing.screenPadding.horizontal,
            marginTop: spacing.sm,
            paddingVertical: spacing.md,
            borderRadius: 12,
            borderWidth: 1.5,
            borderColor: colors.neonCyan,
            alignItems: 'center' as const,
            flexDirection: 'row' as const,
            justifyContent: 'center' as const,
            gap: 8,
          }}
        >
          {isProcessing ? (
            <ActivityIndicator color={colors.neonCyan} size="small" />
          ) : (
            <Text style={{ fontSize: 18, color: colors.neonCyan }}>＋</Text>
          )}
          <Text
            style={{
              color: colors.neonCyan,
              fontFamily: typography.fontFamily.bodyBold,
              fontSize: 15,
            }}
          >
            {isProcessing ? 'Processing…' : 'Add Payment Method'}
          </Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
};
