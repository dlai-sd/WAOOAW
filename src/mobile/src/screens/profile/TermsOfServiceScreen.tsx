/**
 * Terms of Service Screen — placeholder
 * Full content to be added in a future iteration.
 */

import React from 'react';
import { View, Text, SafeAreaView, TouchableOpacity, ScrollView } from 'react-native';
import { useTheme } from '@/hooks/useTheme';
import type { ProfileStackScreenProps } from '@/navigation/types';

type Props = ProfileStackScreenProps<'TermsOfService'>;

export const TermsOfServiceScreen = ({ navigation }: Props) => {
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
          Terms of Service
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
          Our terms of service are available at https://waooaw.com/terms.{'\n\n'}
          By using WAOOAW, you agree to these terms. Full terms document
          coming soon.
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
};
