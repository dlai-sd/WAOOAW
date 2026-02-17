import React, { useState, useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View, ActivityIndicator } from 'react-native';
import * as Font from 'expo-font';
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
import { ThemeProvider, useTheme } from './src/theme';

/**
 * Sample component demonstrating theme usage
 */
function WelcomeScreen() {
  const theme = useTheme();

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={[styles.card, { backgroundColor: theme.colors.card }]}>
        <Text
          style={[
            theme.textVariants.hero,
            { color: theme.colors.neonCyan, marginBottom: theme.spacing.md },
          ]}
        >
          WAOOAW
        </Text>
        <Text
          style={[
            theme.textVariants.h2,
            { color: theme.colors.textPrimary, marginBottom: theme.spacing.sm },
          ]}
        >
          Agents Earn Your Business
        </Text>
        <Text
          style={[
            theme.textVariants.body,
            { color: theme.colors.textSecondary, textAlign: 'center' },
          ]}
        >
          Mobile app theme system loaded successfully!
        </Text>
        
        {/* Status indicators demo */}
        <View style={{ flexDirection: 'row', marginTop: theme.spacing.xl, gap: theme.spacing.sm }}>
          <View style={[styles.statusDot, { backgroundColor: theme.colors.statusOnline }]} />
          <View style={[styles.statusDot, { backgroundColor: theme.colors.statusWorking }]} />
          <View style={[styles.statusDot, { backgroundColor: theme.colors.statusOffline }]} />
        </View>
      </View>
      <StatusBar style="light" />
    </View>
  );
}

/**
 * App component with font loading
 */
export default function App() {
  const [fontsLoaded, setFontsLoaded] = useState(false);

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

  if (!fontsLoaded) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#00f2fe" />
        <Text style={styles.loadingText}>Loading WAOOAW...</Text>
      </View>
    );
  }

  return (
    <ThemeProvider>
      <WelcomeScreen />
    </ThemeProvider>
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
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
  },
  card: {
    padding: 24,
    borderRadius: 20,
    alignItems: 'center',
    minWidth: 300,
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
});
