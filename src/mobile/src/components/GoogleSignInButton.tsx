/**
 * Google Sign In Button Component
 * Branded button following Google's Sign-In branding guidelines
 */

import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  View,
} from 'react-native';
import { Image } from 'expo-image';
import { useTheme } from '../hooks/useTheme';

/**
 * Google Sign In Button Props
 */
interface GoogleSignInButtonProps {
  onPress: () => void;
  loading?: boolean;
  disabled?: boolean;
  style?: any;
}

/**
 * Google Sign In Button
 * 
 * Follows Google's branding guidelines:
 * - White background
 * - Google logo on left
 * - "Sign in with Google" text
 * - Blue border on press
 */
export const GoogleSignInButton: React.FC<GoogleSignInButtonProps> = ({
  onPress,
  loading = false,
  disabled = false,
  style,
}) => {
  const { colors, spacing } = useTheme();

  return (
    <TouchableOpacity
      style={[
        styles.button,
        disabled && styles.buttonDisabled,
        style,
      ]}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.8}
      accessibilityLabel="Sign in with Google"
      accessibilityRole="button"
      accessibilityState={{ disabled: disabled || loading }}
    >
      {loading ? (
        <ActivityIndicator color="#4285F4" size="small" />
      ) : (
        <View style={styles.content}>
          {/* Google Logo */}
          <View style={styles.logoContainer}>
            <Text style={styles.googleLogo}>G</Text>
          </View>
          
          {/* Button Text */}
          <Text style={styles.buttonText}>Sign in with Google</Text>
        </View>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    paddingVertical: 14,
    paddingHorizontal: 24,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 52,
    width: '100%',
    maxWidth: 400,
    // Shadow for depth
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoContainer: {
    width: 24,
    height: 24,
    marginRight: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  googleLogo: {
    fontSize: 20,
    fontWeight: '700',
    color: '#4285F4',
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#3C4043',
    letterSpacing: 0.25,
  },
});

export default GoogleSignInButton;
