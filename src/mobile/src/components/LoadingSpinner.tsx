/**
 * Loading Spinner Component
 * 
 * Full-screen loading indicator for data fetching
 */

import React from 'react';
import { View, ActivityIndicator, Text, StyleSheet } from 'react-native';
import { useTheme } from '../hooks/useTheme';

interface LoadingSpinnerProps {
  message?: string;
}

export const LoadingSpinner = ({ message = 'Loading...' }: LoadingSpinnerProps) => {
  const { colors, spacing, typography } = useTheme();

  return (
    <View style={[styles.container, { backgroundColor: colors.black }]}>
      <ActivityIndicator size="large" color={colors.neonCyan} />
      <Text
        style={[
          styles.message,
          {
            color: colors.textSecondary,
            fontSize: 16,
            fontFamily: typography.fontFamily.body,
            marginTop: spacing.md,
          },
        ]}
      >
        {message}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  message: {},
});
