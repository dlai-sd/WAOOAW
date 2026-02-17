/**
 * Sign In Screen
 * Entry point for user authentication via Google OAuth2
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  Image,
  StyleSheet,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { GoogleSignInButton } from '../../components/GoogleSignInButton';
import { useGoogleAuth } from '../../hooks/useGoogleAuth';
import AuthService from '../../services/auth.service';
import { useTheme } from '../../hooks/useTheme';

/**
 * Sign In Screen Props
 */
interface SignInScreenProps {
  onSignUpPress?: () => void;
  onSignInSuccess?: () => void;
}

/**
 * Sign In Screen Component
 * 
 * Features:
 * - WAOOAW branding (logo, tagline)
 * - Google Sign-In button
 * - Loading states
 * - Error handling
 * - Sign Up link
 * - Dark theme
 * - Safe area insets
 * - Keyboard-aware
 */
export const SignInScreen: React.FC<SignInScreenProps> = ({
  onSignUpPress,
  onSignInSuccess,
}) => {
  const { colors, typography, spacing } = useTheme();
  const {
    promptAsync,
    loading: oauthLoading,
    error: oauthError,
    idToken,
  } = useGoogleAuth();
  const [isSigningIn, setIsSigningIn] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  /**
   * Handle Google Sign In
   * Triggers the OAuth2 flow
   */
  const handleGoogleSignIn = async () => {
    try {
      setErrorMessage(null);
      await promptAsync();
    } catch (error: any) {
      console.error('Failed to start OAuth flow:', error);
      setErrorMessage('Failed to start sign-in. Please try again.');
    }
  };

  /**
   * Exchange ID token for backend JWT
   * Triggered when idToken is received from OAuth
   */
  useEffect(() => {
    const exchangeToken = async () => {
      if (!idToken) return;
      
      try {
        setIsSigningIn(true);
        setErrorMessage(null);

        // Send ID token to backend for verification and JWT exchange
        await AuthService.loginWithGoogle(idToken);

        // Navigate to main app
        if (onSignInSuccess) {
          onSignInSuccess();
        }
      } catch (error: any) {
        console.error('Backend authentication failed:', error);
        
        // Handle specific error codes
        if (error.code === '2FA_REQUIRED') {
          Alert.alert(
            '2FA Required',
            'This account requires two-factor authentication. Please enter your 2FA code.',
            [{ text: 'OK' }]
          );
        } else {
          const message = error.message || 'Authentication failed. Please try again.';
          setErrorMessage(message);
          Alert.alert('Sign In Failed', message, [{ text: 'OK' }]);
        }
      } finally {
        setIsSigningIn(false);
      }
    };

    exchangeToken();
  }, [idToken, onSignInSuccess]);

  /**
   * Handle OAuth errors from hook
   */
  useEffect(() => {
    if (oauthError) {
      // Only show error if not a user cancellation
      if (oauthError.code !== 'USER_CANCELLED') {
        setErrorMessage(oauthError.message);
      }
    }
  }, [oauthError]);

  const isLoading = oauthLoading || isSigningIn;

  return (
    <SafeAreaView
      style={[styles.safeArea, { backgroundColor: colors.black }]}
      edges={['top', 'bottom', 'left', 'right']}
    >
      <KeyboardAvoidingView
        style={styles.keyboardAvoid}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <View style={[styles.container, { paddingHorizontal: spacing.screenPadding }]}>
            {/* Logo Section */}
            <View style={styles.logoSection}>
              <View style={styles.logoContainer}>
                <Text style={[styles.logoText, { color: colors.neonCyan }]}>
                  WAOOAW
                </Text>
              </View>
              
              <Text
                style={[
                  styles.title,
                  {
                    fontFamily: typography.fontFamily.display,
                    color: colors.textPrimary,
                    marginTop: spacing.lg,
                  },
                ]}
              >
                Welcome Back
              </Text>
              
              <Text
                style={[
                  styles.subtitle,
                  {
                    fontFamily: typography.fontFamily.body,
                    color: colors.textSecondary,
                    marginTop: spacing.xs,
                  },
                ]}
              >
                Agents Earn Your Business
              </Text>
            </View>

            {/* Sign In Button Section */}
            <View style={[styles.buttonSection, { marginTop: spacing.xxl }]}>
              <GoogleSignInButton
                onPress={handleGoogleSignIn}
                loading={isLoading}
                disabled={isLoading}
              />
              
              {/* Error Message */}
              {errorMessage && (
                <View
                  style={[
                    styles.errorContainer,
                    {
                      backgroundColor: `${colors.error}15`,
                      borderColor: colors.error,
                      marginTop: spacing.md,
                      borderRadius: 8,
                      padding: spacing.md,
                      borderWidth: 1,
                    },
                  ]}
                >
                  <Text style={[styles.errorText, { color: colors.error }]}>
                    {errorMessage}
                  </Text>
                </View>
              )}
            </View>

            {/* Sign Up Link */}
            <View style={[styles.footer, { marginTop: spacing.xl }]}>
              <Text
                style={[
                  styles.footerText,
                  {
                    fontFamily: typography.fontFamily.body,
                    color: colors.textSecondary,
                  },
                ]}
              >
                Don't have an account?{' '}
              </Text>
              <TouchableOpacity
                onPress={onSignUpPress}
                disabled={isLoading}
                accessibilityLabel="Sign up"
                accessibilityRole="button"
                accessibilityState={{ disabled: isLoading }}
              >
                <Text
                  style={[
                    styles.footerLink,
                    {
                      fontFamily: typography.fontFamily.bodyBold,
                      color: colors.neonCyan,
                    },
                  ]}
                >
                  Sign up
                </Text>
              </TouchableOpacity>
            </View>

            {/* Tagline */}
            <Text
              style={[
                styles.tagline,
                {
                  fontFamily: typography.fontFamily.body,
                  color: colors.textSecondary,
                  marginTop: spacing.xxl,
                },
              ]}
            >
              The First AI Agent Marketplace
            </Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
  },
  keyboardAvoid: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
  },
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 48,
  },
  logoSection: {
    alignItems: 'center',
  },
  logoContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoText: {
    fontSize: 48,
    fontWeight: '700',
    letterSpacing: 2,
  },
  title: {
    fontSize: 32,
    fontWeight: '700',
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
  },
  buttonSection: {
    width: '100%',
    alignItems: 'center',
  },
  errorContainer: {
    width: '100%',
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  footerText: {
    fontSize: 14,
  },
  footerLink: {
    fontSize: 14,
  },
  tagline: {
    fontSize: 12,
    textAlign: 'center',
    opacity: 0.6,
  },
});

export default SignInScreen;
