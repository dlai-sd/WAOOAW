import React, { useState, useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, View, ActivityIndicator, Text } from 'react-native';
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
import { ThemeProvider } from './src/theme';
import { RootNavigator } from './src/navigation/RootNavigator';

/**
 * App component with font loading and navigation
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
      <RootNavigator />
      <StatusBar style="light" />
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
});
