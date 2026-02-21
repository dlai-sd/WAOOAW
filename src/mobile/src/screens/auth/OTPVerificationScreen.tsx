/**
 * OTP Verification Screen
 * Verifies OTP code sent via email/phone after registration
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '../../hooks/useTheme';
import { OTPInput } from '../../components/OTPInput';
import RegistrationService, {
  RegistrationServiceError,
  RegistrationErrorCode,
} from '../../services/registration.service';

export interface OTPVerificationScreenProps {
  /**
   * Registration ID from sign up
   */
  registrationId: string;
  
  /**
   * OTP ID from start OTP
   */
  otpId: string;
  
  /**
   * Channel used (email or phone)
   */
  channel?: 'email' | 'phone' | 'sms';
  
  /**
   * Masked destination (e.g., "j***n@example.com")
   */
  destinationMasked?: string;
  
  /**
   * Callback when verification is successful
   */
  onVerificationSuccess?: () => void;
  
  /**
   * Callback to go back to sign up
   */
  onBack?: () => void;
}

export const OTPVerificationScreen: React.FC<OTPVerificationScreenProps> = ({
  registrationId,
  otpId: initialOtpId,
  channel,
  destinationMasked,
  onVerificationSuccess,
  onBack,
}) => {
  const { colors, spacing, typography } = useTheme();
  
  const [otpId, setOtpId] = useState(initialOtpId);
  const [isVerifying, setIsVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [canResend, setCanResend] = useState(true);
  const [resendCountdown, setResendCountdown] = useState(0);
  const [isResending, setIsResending] = useState(false);
  const [resendSuccessMessage, setResendSuccessMessage] = useState<string | null>(null);
  const resendResetTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (resendResetTimerRef.current) {
        clearTimeout(resendResetTimerRef.current);
      }
    };
  }, []);

  /**
   * Countdown timer for resend button
   */
  useEffect(() => {
    if (resendCountdown > 0) {
      const timer = setTimeout(() => {
        setResendCountdown(resendCountdown - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else {
      setCanResend(true);
    }
  }, [resendCountdown]);

  /**
   * Handle OTP complete
   */
  const handleOTPComplete = async (code: string) => {
    setIsVerifying(true);
    setError(null);

    try {
      // Verify OTP with backend
      await RegistrationService.verifyOTP(otpId, code);
      
      // Success! Tokens are automatically saved by the service
      if (onVerificationSuccess) {
        onVerificationSuccess();
      } else {
        Alert.alert(
          'Verification Successful',
          'Your account has been created!',
          [{ text: 'OK' }]
        );
      }
    } catch (err: any) {
      console.error('OTP verification error:', err);

      const errorCode = err?.code;
      const isRegistrationServiceError =
        typeof RegistrationServiceError === 'function' && err instanceof RegistrationServiceError;

      if (isRegistrationServiceError || typeof errorCode === 'string') {
        switch (errorCode) {
          case RegistrationErrorCode.INVALID_OTP_CODE:
          case 'INVALID_OTP':
            setError('Invalid code. Please try again.');
            break;
          case RegistrationErrorCode.OTP_EXPIRED:
          case 'OTP_EXPIRED':
            setError('Code expired. Please request a new one.');
            setCanResend(true);
            setResendCountdown(0);
            break;
          case RegistrationErrorCode.TOO_MANY_ATTEMPTS:
          case 'TOO_MANY_ATTEMPTS':
            setError('Too many attempts. Please request a new code.');
            break;
          default:
            setError(err.message);
        }
      } else {
        setError('Verification failed. Please try again.');
      }
    } finally {
      setIsVerifying(false);
    }
  };

  /**
   * Handle resend OTP
   */
  const handleResend = async () => {
    if (!canResend || isResending || isVerifying) {
      return;
    }

    setIsResending(true);
    setError(null);
    setResendSuccessMessage(null);

    try {
      // Request new OTP
      const response = channel
        ? await RegistrationService.startOTP(registrationId, channel as any)
        : await RegistrationService.startOTP(registrationId);
      
      // Update OTP ID and reset countdown
      setOtpId(response.otp_id);
      setResendCountdown(30);
      setCanResend(false);

      if (resendResetTimerRef.current) {
        clearTimeout(resendResetTimerRef.current);
      }
      resendResetTimerRef.current = setTimeout(() => {
        setResendCountdown(0);
        setCanResend(true);
      }, 30000);
      
      setResendSuccessMessage('Code sent successfully!');
    } catch (err: any) {
      console.error('Resend OTP error:', err);
      
      const isRegistrationServiceError =
        typeof RegistrationServiceError === 'function' && err instanceof RegistrationServiceError;

      if (isRegistrationServiceError) {
        if (err.code === RegistrationErrorCode.TOO_MANY_ATTEMPTS) {
          setError('Too many requests. Please wait and try again.');
        } else {
          setError(err.message);
        }
      } else {
        setError('Failed to resend code. Please try again.');
      }
    } finally {
      setIsResending(false);
    }
  };

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: colors.black }]}
      edges={['top', 'left', 'right', 'bottom']}
    >
      <View
        style={[
          styles.content,
          {
            paddingHorizontal: spacing.screenPadding.horizontal,
            paddingVertical: spacing.screenPadding.vertical,
          },
        ]}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text
            style={[
              styles.logo,
              {
                fontFamily: typography.fontFamily.display,
                color: colors.neonCyan,
                marginBottom: spacing.xl,
              },
            ]}
          >
            WAOOAW
          </Text>
          
          <Text
            style={[
              styles.title,
              {
                fontFamily: typography.fontFamily.display,
                color: colors.textPrimary,
                marginBottom: spacing.md,
              },
            ]}
          >
            Verify Your Account
          </Text>
          
          <Text
            style={[
              styles.subtitle,
              {
                fontFamily: typography.fontFamily.body,
                color: colors.textSecondary,
              },
            ]}
          >
            Enter the 6-digit code sent to
          </Text>
          
          {destinationMasked && (
            <Text
              style={[
                styles.destination,
                {
                  fontFamily: typography.fontFamily.bodyBold,
                  color: colors.textPrimary,
                  marginTop: spacing.xs,
                },
              ]}
            >
              {destinationMasked}
            </Text>
          )}
        </View>

        {/* OTP Input */}
        <View style={[styles.otpContainer, { marginTop: spacing.xxl }]}>
          <OTPInput
            length={6}
            onComplete={handleOTPComplete}
            onChange={() => {
              if (error) {
                setError(null);
              }
            }}
            disabled={isVerifying}
            error={!!error}
            autoFocus
          />
        </View>

        {/* Error Message */}
        {error && (
          <View
            style={[
              styles.errorContainer,
              {
                backgroundColor: colors.error + '20',
                marginTop: spacing.lg,
              },
            ]}
          >
            <Text
              style={[
                styles.errorText,
                {
                  fontFamily: typography.fontFamily.body,
                  color: colors.error,
                },
              ]}
            >
              {error}
            </Text>
          </View>
        )}

        {resendSuccessMessage && (
          <Text
            style={{
              color: colors.neonCyan,
              textAlign: 'center',
              marginTop: spacing.md,
              fontFamily: typography.fontFamily.body,
            }}
          >
            {resendSuccessMessage}
          </Text>
        )}

        {/* Loading State */}
        {isVerifying && (
          <View style={[styles.loadingContainer, { marginTop: spacing.lg }]}>
            <ActivityIndicator color={colors.neonCyan} size="small" />
            <Text
              style={[
                styles.loadingText,
                {
                  fontFamily: typography.fontFamily.body,
                  color: colors.textSecondary,
                  marginLeft: spacing.sm,
                },
              ]}
            >
              Verifying...
            </Text>
          </View>
        )}

        {/* Resend OTP */}
        <View style={[styles.resendContainer, { marginTop: spacing.xl }]}>
          <Text
            style={[
              styles.resendText,
              {
                fontFamily: typography.fontFamily.body,
                color: colors.textSecondary,
              },
            ]}
          >
            Didn't receive the code?{' '}
          </Text>
          
          {canResend && !isResending ? (
            <TouchableOpacity
              onPress={handleResend}
              accessibilityLabel="Resend Code"
              accessibilityRole="button"
              accessibilityState={{ disabled: isVerifying }}
            >
              <Text
                style={[
                  styles.resendLink,
                  {
                    fontFamily: typography.fontFamily.bodyBold,
                    color: colors.neonCyan,
                  },
                ]}
              >
                Resend Code
              </Text>
            </TouchableOpacity>
          ) : (
            <TouchableOpacity
              disabled
              accessibilityState={{ disabled: true }}
            >
              <Text
                style={[
                  styles.resendDisabled,
                  {
                    fontFamily: typography.fontFamily.body,
                    color: colors.textSecondary + '80',
                  },
                ]}
              >
                {isResending ? 'Sending...' : `Resend in ${resendCountdown}s`}
              </Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Back Button */}
        {onBack && (
          <TouchableOpacity
            onPress={() => {
              if (!isVerifying) {
                onBack();
              }
            }}
            style={[styles.backButton, { marginTop: spacing.xl }]}
            disabled={isVerifying}
            accessibilityLabel="Go back"
            accessibilityRole="button"
          >
            <Text
              style={[
                styles.backButtonText,
                {
                  fontFamily: typography.fontFamily.body,
                  color: colors.textSecondary,
                },
              ]}
            >
              ← Back to Sign Up
            </Text>
          </TouchableOpacity>
        )}
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
  },
  header: {
    alignItems: 'center',
  },
  logo: {
    fontSize: 48,
    fontWeight: '700',
    letterSpacing: 2,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
  },
  destination: {
    fontSize: 16,
    textAlign: 'center',
  },
  otpContainer: {
    alignItems: 'center',
  },
  errorContainer: {
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
  },
  loadingContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 14,
  },
  resendContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  resendText: {
    fontSize: 14,
  },
  resendLink: {
    fontSize: 14,
  },
  resendDisabled: {
    fontSize: 14,
  },
  backButton: {
    alignSelf: 'center',
    padding: 12,
  },
  backButtonText: {
    fontSize: 14,
  },
});
