/**
 * Error View Component
 * 
 * Displays error message with retry button
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useTheme } from '../hooks/useTheme';

interface ErrorViewProps {
  message?: string;
  onRetry?: () => void;
}

export const ErrorView = ({ 
  message = 'Something went wrong', 
  onRetry 
}: ErrorViewProps) => {
  const { colors, spacing, typography } = useTheme();

  return (
    <View style={[styles.container, { backgroundColor: colors.black }]}>
      <Text style={{ fontSize: 64, marginBottom: spacing.lg }}>⚠️</Text>
      
      <Text
        style={[
          styles.title,
          {
            color: colors.textPrimary,
            fontSize: 20,
            fontFamily: typography.fontFamily.bodyBold,
            marginBottom: spacing.sm,
            textAlign: 'center',
          },
        ]}
      >
        Oops! An error occurred
      </Text>
      
      <Text
        style={[
          styles.message,
          {
            color: colors.textSecondary,
            fontSize: 14,
            fontFamily: typography.fontFamily.body,
            marginBottom: spacing.lg,
            textAlign: 'center',
            paddingHorizontal: spacing.xl,
          },
        ]}
      >
        {message}
      </Text>

      {onRetry && (
        <TouchableOpacity
          activeOpacity={0.8}
          onPress={onRetry}
          style={[
            styles.retryButton,
            {
              backgroundColor: colors.neonCyan,
              borderRadius: spacing.sm,
              paddingHorizontal: spacing.xl,
              paddingVertical: spacing.md,
            },
          ]}
        >
          <Text
            style={[
              styles.retryText,
              {
                color: colors.black,
                fontSize: 16,
                fontFamily: typography.fontFamily.bodyBold,
              },
            ]}
          >
            Try Again
          </Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 20,
  },
  title: {},
  message: {},
  retryButton: {},
  retryText: {},
});
