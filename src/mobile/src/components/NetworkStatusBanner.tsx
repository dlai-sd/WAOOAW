/**
 * Network Status Banner Component
 * 
 * Shows a banner at the top of the screen when offline
 * Uses network status hook to detect connectivity
 */

import React from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { useNetworkStatus } from '../hooks/useNetworkStatus';
import { useTheme } from '../hooks/useTheme';

export const NetworkStatusBanner = () => {
  const { isOffline, type } = useNetworkStatus();
  const { colors, spacing } = useTheme();
  const slideAnim = React.useRef(new Animated.Value(-50)).current;

  React.useEffect(() => {
    if (isOffline) {
      // Slide down
      Animated.spring(slideAnim, {
        toValue: 0,
        useNativeDriver: true,
        tension: 50,
        friction: 8,
      }).start();
    } else {
      // Slide up
      Animated.timing(slideAnim, {
        toValue: -50,
        duration: 300,
        useNativeDriver: true,
      }).start();
    }
  }, [isOffline, slideAnim]);

  if (!isOffline) {
    return null;
  }

  return (
    <Animated.View
      style={[
        styles.container,
        {
          backgroundColor: '#ef4444',
          transform: [{ translateY: slideAnim }],
        },
      ]}
    >
      <Text style={styles.emoji}>📡</Text>
      <View style={styles.textContainer}>
        <Text style={styles.title}>No Internet Connection</Text>
        <Text style={styles.subtitle}>
          {type === 'none' ? 'You are offline' : 'Limited connectivity'}
        </Text>
      </View>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 1000,
    elevation: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
  },
  emoji: {
    fontSize: 20,
    marginRight: 12,
  },
  textContainer: {
    flex: 1,
  },
  title: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 2,
  },
  subtitle: {
    fontSize: 12,
    color: '#ffffff',
    opacity: 0.9,
  },
});
