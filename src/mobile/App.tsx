import React, { useState, useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, View, ActivityIndicator, Text } from 'react-native';
import * as Font from 'expo-font';
// import * as Sentry from '@sentry/react-native'; // REMOVED for demo build
const Sentry = { wrap: (component: any) => component };
import {
  SpaceGrotesk_700Bold,
} from '@expo-google-fonts/space-grotesk';
import {
  Outfit_600SemiBold,
} from '@expo-google-fonts/outfit';
import {
  Inter_400Regular,
  Inter_600SemiBold,
} from '@expo-google-fonts/inter';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from './src/theme';
import { RootNavigator } from './src/navigation/RootNavigator';
import { ErrorBoundary } from './src/components/ErrorBoundary';
import { initSentry, setSentryUser, clearSentryUser } from './src/config/sentry.config';
import { analyticsService } from './src/services/analytics/firebase.analytics';
import { crashlyticsService } from './src/services/monitoring/crashlytics.service';
import { performanceService } from './src/services/monitoring/performance.service';
import { useAuthStore } from './src/store/authStore';

// Initialize Sentry BEFORE App component renders
initSentry();

/**
 * React Query client configuration
 */
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 1000 * 60 * 5, // 5 minutes default
      gcTime: 1000 * 60 * 30, // 30 minutes default
      refetchOnWindowFocus: true,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
    },
  },
});

/**
 * App component with font loading and navigation
 */
function AppComponent() {
  const [fontsLoaded, setFontsLoaded] = useState(false);
  const user = useAuthStore((state) => state.user);

  // Initialize fonts
  useEffect(() => {
    async function loadFonts() {
      try {
        await Font.loadAsync({
          SpaceGrotesk_700Bold,
          Outfit_600SemiBold,
          Inter_400Regular,
          Inter_600SemiBold,
        });
        setFontsLoaded(true);
      } catch (error) {
        console.error('Error loading fonts:', error);
        // Continue anyway for development
        setFontsLoaded(true);
      }
    }

    loadFonts();
  }, []);

  // Initialize monitoring services
  useEffect(() => {
    async function initializeMonitoring() {
      try {
        console.log('[App] Initializing monitoring services...');
        console.log('[App] API URL:', process.env.EXPO_PUBLIC_API_URL || 'Using environment.config.ts');
        
        // Skip monitoring in development without crashing
        if (__DEV__) {
          console.log('[App] Skipping monitoring initialization in development mode');
          return;
        }
        
        await Promise.all([
          analyticsService.initialize(),
          crashlyticsService.initialize(),
          performanceService.initialize(),
        ]);
        console.log('[App] Monitoring services initialized successfully');
      } catch (error) {
        console.error('[App] Failed to initialize monitoring:', error);
        // Don't block app from starting
      }
    }

    initializeMonitoring();
  }, []);

  // Update user context for monitoring when auth state changes
  useEffect(() => {
    if (user) {
      // Set user context in all monitoring services
      console.log(`[App] Setting user context: ${user.id}`);
      crashlyticsService.setUser(user.id, user.email, user.full_name);
      setSentryUser(user.id, user.email);
      analyticsService.setUserId(user.id);
      
      if (user.email) {
        analyticsService.setUserProperty('email_domain', user.email.split('@')[1]);
      }
    } else {
      // Clear user context on sign out
      console.log('[App] Clearing user context');
      crashlyticsService.clearUser();
      clearSentryUser();
    }
  }, [user]);

  if (!fontsLoaded) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#00f2fe" />
        <Text style={styles.loadingText}>Loading WAOOAW...</Text>
      </View>
    );
  }

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <RootNavigator />
          <StatusBar style="light" />
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    backgroundColor: '#0a0a0a',
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    marginTop: 16,
    color: '#ffffff',
    fontSize: 16,
  },
});

// Wrap App with Sentry for error tracking
export default Sentry.wrap(AppComponent);
