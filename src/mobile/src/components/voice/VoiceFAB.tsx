/**
 * VoiceFAB Component
 * Floating Action Button for voice command activation
 * 
 * Features:
 * - Tap to start/stop voice recognition
 * - Visual feedback (pulsing animation when listening)
 * - Error state indication
 * - Haptic feedback
 * - Accessible
 */

import React, { useEffect, useRef } from 'react';
import {
  View,
  TouchableOpacity,
  StyleSheet,
  Animated,
  ViewStyle,
  Platform,
} from 'react-native';
import { useTheme } from '../../hooks/useTheme';

export interface VoiceFABProps {
  isListening?: boolean;
  isProcessing?: boolean;
  hasError?: boolean;
  disabled?: boolean;
  onPress: () => void;
  style?: ViewStyle;
  size?: 'small' | 'medium' | 'large';
  position?: 'bottom-right' | 'bottom-center' | 'bottom-left';
}

export function VoiceFAB({
  isListening = false,
  isProcessing = false,
  hasError = false,
  disabled = false,
  onPress,
  style,
  size = 'large',
  position = 'bottom-right',
}: VoiceFABProps): React.JSX.Element {
  const theme = useTheme();
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const rotateAnim = useRef(new Animated.Value(0)).current;

  // Pulsing animation when listening
  useEffect(() => {
    if (isListening) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.2,
            duration: 800,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 800,
            useNativeDriver: true,
          }),
        ])
      ).start();
    } else {
      pulseAnim.setValue(1);
    }
  }, [isListening, pulseAnim]);

  // Rotating animation when processing
  useEffect(() => {
    if (isProcessing) {
      Animated.loop(
        Animated.timing(rotateAnim, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        })
      ).start();
    } else {
      rotateAnim.setValue(0);
    }
  }, [isProcessing, rotateAnim]);

  const sizes = {
    small: 48,
    medium: 56,
    large: 64,
  };

  const buttonSize = sizes[size];

  const rotate = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  const positionStyles: Record<string, ViewStyle> = {
    'bottom-right': {
      position: 'absolute',
      bottom: 24,
      right: 24,
    },
    'bottom-center': {
      position: 'absolute',
      bottom: 24,
      left: '50%',
      marginLeft: -buttonSize / 2,
    },
    'bottom-left': {
      position: 'absolute',
      bottom: 24,
      left: 24,
    },
  };

  const getBackgroundColor = () => {
    if (disabled) return theme.colors.border;
    if (hasError) return theme.colors.error;
    if (isListening) return theme.colors.neonCyan;
    return theme.colors.neonPurple;
  };

  return (
    <View style={[positionStyles[position], style]}>
      {/* Outer glow ring when listening */}
      {isListening && (
        <Animated.View
          style={[
            styles.glowRing,
            {
              width: buttonSize + 16,
              height: buttonSize + 16,
              borderRadius: (buttonSize + 16) / 2,
              backgroundColor: theme.colors.neonCyan,
              opacity: pulseAnim.interpolate({
                inputRange: [1, 1.2],
                outputRange: [0.3, 0],
              }),
              transform: [{ scale: pulseAnim }],
            },
          ]}
        />
      )}

      {/* Main button */}
      <Animated.View
        style={{
          transform: [
            { scale: pulseAnim },
            { rotate: isProcessing ? rotate : '0deg' },
          ],
        }}
      >
        <TouchableOpacity
          onPress={onPress}
          disabled={disabled}
          activeOpacity={0.8}
          accessibilityLabel="Voice command button"
          accessibilityHint="Tap to start voice command"
          accessibilityRole="button"
          accessibilityState={{
            disabled,
            busy: isProcessing,
            selected: isListening,
          }}
          style={[
            styles.button,
            {
              width: buttonSize,
              height: buttonSize,
              borderRadius: buttonSize / 2,
              backgroundColor: getBackgroundColor(),
              ...Platform.select({
                ios: {
                  shadowColor: isListening ? theme.colors.neonCyan : '#000',
                  shadowOffset: { width: 0, height: 4 },
                  shadowOpacity: isListening ? 0.5 : 0.3,
                  shadowRadius: isListening ? 12 : 8,
                },
                android: {
                  elevation: isListening ? 12 : 8,
                },
              }),
            },
          ]}
        >
          {/* Microphone Icon */}
          <View style={styles.iconContainer}>
            {isProcessing ? (
              <View style={[styles.processingDot, { backgroundColor: theme.colors.background }]} />
            ) : (
              <View style={styles.microphoneIcon}>
                {/* Simple microphone shape */}
                <View
                  style={[
                    styles.micBody,
                    { backgroundColor: theme.colors.background },
                  ]}
                />
                <View
                  style={[
                    styles.micBase,
                    { borderColor: theme.colors.background },
                  ]}
                />
              </View>
            )}
          </View>
        </TouchableOpacity>
      </Animated.View>

      {/* Status indicator dot */}
      {(isListening || hasError) && (
        <View
          style={[
            styles.statusDot,
            {
              backgroundColor: hasError
                ? theme.colors.error
                : theme.colors.success,
            },
          ]}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  button: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  glowRing: {
    position: 'absolute',
    top: -8,
    left: -8,
  },
  iconContainer: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  microphoneIcon: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  micBody: {
    width: 16,
    height: 24,
    borderRadius: 8,
  },
  micBase: {
    width: 20,
    height: 12,
    borderTopWidth: 3,
    borderLeftWidth: 3,
    borderRightWidth: 3,
    borderBottomWidth: 0,
    borderTopLeftRadius: 10,
    borderTopRightRadius: 10,
    marginTop: 2,
  },
  processingDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  statusDot: {
    position: 'absolute',
    top: 4,
    right: 4,
    width: 12,
    height: 12,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: '#fff',
  },
});
