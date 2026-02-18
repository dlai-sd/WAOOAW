/**
 * Root Navigator
 * 
 * Top-level navigation that conditionally renders Auth or Main flow
 * based on authentication state
 */

import React, { useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { AuthNavigator } from './AuthNavigator';
import { MainNavigator } from './MainNavigator';
import { useAuthStore } from '../store/authStore';
import { useTheme } from '../hooks/useTheme';
import { NetworkStatusBanner } from '../components/NetworkStatusBanner';
import { linking } from './types';

/**
 * Loading Screen
 * Shown while checking authentication state on app startup
 */
const LoadingScreen = () => {
  const { colors } = useTheme();
  
  return (
    <View style={[styles.loadingContainer, { backgroundColor: colors.black }]}>
      <ActivityIndicator size="large" color={colors.neonCyan} />
    </View>
  );
};

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

/**
 * Root Navigator
 * 
 * Handles:
 * - Authentication state initialization
 * - Conditional navigation (Auth vs Main)
 * - Deep linking configuration
 */
export const RootNavigator = () => {
  const { colors } = useTheme();
  const { isAuthenticated, isLoading, initialize } = useAuthStore();

  // Initialize auth state on mount
  useEffect(() => {
    initialize();
  }, [initialize]);

  // Show loading screen while checking auth state
  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <View style={{ flex: 1 }}>
      <NavigationContainer
        linking={linking}
        theme={{
          dark: true,
          colors: {
            primary: colors.neonCyan,
            background: colors.black,
            card: colors.black,
            text: colors.textPrimary,
            border: colors.textSecondary + '40', // 40% opacity
            notification: colors.neonCyan,
          },
        }}
      >
        {isAuthenticated ? <MainNavigator /> : <AuthNavigator />}
      </NavigationContainer>
      <NetworkStatusBanner />
    </View>
  );
};
