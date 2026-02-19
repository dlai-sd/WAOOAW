/**
 * Empty State Component
 * 
 * Displays message when no data is available
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useTheme } from '../hooks/useTheme';

interface EmptyStateProps {
  message?: string;
  icon?: string;
  subtitle?: string;
}

export const EmptyState = ({ 
  message = 'No data available',
  icon = '📭',
  subtitle 
}: EmptyStateProps) => {
  const { colors, spacing, typography } = useTheme();

  return (
    <View style={styles.container}>
      <Text style={{ fontSize: 64, marginBottom: spacing.lg }}>{icon}</Text>
      
      <Text
        style={[
          styles.message,
          {
            color: colors.textPrimary,
            fontSize: 18,
            fontFamily: typography.fontFamily.bodyBold,
            marginBottom: subtitle ? spacing.sm : 0,
            textAlign: 'center',
          },
        ]}
      >
        {message}
      </Text>

      {subtitle && (
        <Text
          style={[
            styles.subtitle,
            {
              color: colors.textSecondary,
              fontSize: 14,
              fontFamily: typography.fontFamily.body,
              textAlign: 'center',
              paddingHorizontal: spacing.xl,
            },
          ]}
        >
          {subtitle}
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
    paddingHorizontal: 20,
  },
  message: {},
  subtitle: {},
});
