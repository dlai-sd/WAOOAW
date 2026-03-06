/**
 * Privacy Policy Screen — placeholder
 * Full content to be added in a future iteration.
 */

import React from 'react';
import { View, Text, SafeAreaView, TouchableOpacity, ScrollView } from 'react-native';
import { useTheme } from '@/hooks/useTheme';
import type { ProfileStackScreenProps } from '@/navigation/types';

type Props = ProfileStackScreenProps<'PrivacyPolicy'>;

export const PrivacyPolicyScreen = ({ navigation }: Props) => {
  const { colors, spacing, typography } = useTheme();

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
          Privacy Policy
        </Text>
      </View>
      <ScrollView
        contentContainerStyle={{
          padding: spacing.screenPadding.horizontal,
        }}
      >
        <Text
          style={{
            color: colors.textSecondary,
            fontFamily: typography.fontFamily.body,
            fontSize: 14,
            lineHeight: 22,
          }}
        >
          Our privacy policy is available at https://waooaw.com/privacy.{'\n\n'}
          We are committed to protecting your personal data in accordance with
          applicable data protection laws. Full policy document coming soon.
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
};
