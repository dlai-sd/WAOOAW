/**
 * Sign Up Screen
 * Customer registration with email/phone and OTP verification
 * Uses CP backend registration flow (no password required)
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '../../hooks/useTheme';
import RegistrationService, {
  RegistrationServiceError,
  RegistrationErrorCode,
} from '../../services/registration.service';

export interface SignUpScreenProps {
  /**
   * Callback when user wants to sign in instead
   */
  onSignInPress?: () => void;
  
  /**
   * Callback when registration is successful (before OTP)
   */
  onRegistrationSuccess?: (registrationId: string, otpId: string) => void;
}

interface FormData {
  fullName: string;
  email: string;
  phone: string;
  businessName: string;
}

interface FormErrors {
  fullName?: string;
  email?: string;
  phone?: string;
}

export const SignUpScreen: React.FC<SignUpScreenProps> = ({
  onSignInPress,
  onRegistrationSuccess,
}) => {
  const { colors, spacing, typography } = useTheme();
  
  // Form state
  const [formData, setFormData] = useState<FormData>({
    fullName: '',
    email: '',
    phone: '',
    businessName: '',
  });
  
  const [errors, setErrors] = useState<FormErrors>({});
  const [isRegistering, setIsRegistering] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);

  /**
   * Validate form fields
   */
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};
    
    // Full name validation
    if (!formData.fullName.trim()) {
      newErrors.fullName = 'Full name is required';
    } else if (formData.fullName.trim().length < 2) {
      newErrors.fullName = 'Name must be at least 2 characters';
    }
    
    // Email validation
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }
    
    // Phone validation (E.164 format)
    if (!formData.phone.trim()) {
      newErrors.phone = 'Phone is required';
    } else if (!/^\+?[1-9]\d{1,14}$/.test(formData.phone.replace(/[\s\-()]/g, ''))) {
      newErrors.phone = 'Invalid phone format (use +91XXXXXXXXXX)';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * Handle input change
   */
  const handleInputChange = (field: keyof FormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    
    // Clear field error on change
    if (errors[field as keyof FormErrors]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field as keyof FormErrors];
        return newErrors;
      });
    }
    
    // Clear general error
    if (generalError) {
      setGeneralError(null);
    }
  };

  /**
   * Handle sign up
   */
  const handleSignUp = async () => {
    // Validate form
    if (!validateForm()) {
      return;
    }

    setIsRegistering(true);
    setGeneralError(null);

    try {
      // Format phone number (ensure E.164 format)
      const phone = formData.phone.trim().startsWith('+')
        ? formData.phone.trim()
        : `+${formData.phone.trim()}`;

      // Register and start OTP
      const { registration, otp } = await RegistrationService.registerAndStartOTP({
        fullName: formData.fullName.trim(),
        email: formData.email.trim().toLowerCase(),
        phone,
        businessName: formData.businessName.trim() || undefined,
      });

      // Success! Navigate to OTP verification
      if (onRegistrationSuccess) {
        onRegistrationSuccess(registration.registration_id, otp.otp_id);
      } else {
        // Show success alert if no navigation handler
        Alert.alert(
          'Registration Successful',
          `OTP sent via ${otp.channel.toUpperCase()} to ${otp.destination_masked}`,
          [{ text: 'OK' }]
        );
      }
    } catch (error) {
      console.error('Registration error:', error);
      
      if (error instanceof RegistrationServiceError) {
        // Handle specific registration errors
        switch (error.code) {
          case RegistrationErrorCode.EMAIL_ALREADY_REGISTERED:
            setErrors({ email: 'Email already registered' });
            setGeneralError('This email is already registered. Please sign in.');
            break;
          case RegistrationErrorCode.PHONE_ALREADY_REGISTERED:
            setErrors({ phone: 'Phone already registered' });
            setGeneralError('This phone is already registered. Please sign in.');
            break;
          case RegistrationErrorCode.INVALID_INPUT:
            setGeneralError(error.message);
            break;
          default:
            setGeneralError(error.message);
        }
      } else {
        setGeneralError('Registration failed. Please try again.');
      }
    } finally {
      setIsRegistering(false);
    }
  };

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: colors.black }]}
      edges={['top', 'left', 'right']}
    >
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView
          contentContainerStyle={[
            styles.scrollContent,
            { paddingHorizontal: spacing.screenPadding },
          ]}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* Header */}
          <View style={[styles.header, { marginTop: spacing.xl }]}>
            <Text
              style={[
                styles.logo,
                {
                  fontFamily: typography.fontFamily.display,
                  color: colors.neonCyan,
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
                  marginTop: spacing.md,
                },
              ]}
            >
              Create Account
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
              Join the AI Agent Marketplace
            </Text>
          </View>

          {/* Form */}
          <View style={[styles.form, { marginTop: spacing.xxl }]}>
            {/* Full Name */}
            <View style={styles.inputGroup}>
              <Text
                style={[
                  styles.label,
                  {
                    fontFamily: typography.fontFamily.bodyBold,
                    color: colors.textPrimary,
                  },
                ]}
              >
                Full Name *
              </Text>
              <TextInput
                value={formData.fullName}
                onChangeText={(value) => handleInputChange('fullName', value)}
                placeholder="John Doe"
                placeholderTextColor={colors.textSecondary + '80'}
                style={[
                  styles.input,
                  {
                    fontFamily: typography.fontFamily.body,
                    color: colors.textPrimary,
                    backgroundColor: colors.black,
                    borderColor: errors.fullName ? colors.error : colors.textSecondary + '40',
                  },
                ]}
                editable={!isRegistering}
                autoCapitalize="words"
                autoComplete="name"
                textContentType="name"
                returnKeyType="next"
                accessibilityLabel="Full Name"
                accessibilityHint="Enter your full name"
              />
              {errors.fullName && (
                <Text
                  style={[
                    styles.errorText,
                    {
                      fontFamily: typography.fontFamily.body,
                      color: colors.error,
                    },
                  ]}
                >
                  {errors.fullName}
                </Text>
              )}
            </View>

            {/* Email */}
            <View style={styles.inputGroup}>
              <Text
                style={[
                  styles.label,
                  {
                    fontFamily: typography.fontFamily.bodyBold,
                    color: colors.textPrimary,
                  },
                ]}
              >
                Email *
              </Text>
              <TextInput
                value={formData.email}
                onChangeText={(value) => handleInputChange('email', value)}
                placeholder="john@example.com"
                placeholderTextColor={colors.textSecondary + '80'}
                style={[
                  styles.input,
                  {
                    fontFamily: typography.fontFamily.body,
                    color: colors.textPrimary,
                    backgroundColor: colors.black,
                    borderColor: errors.email ? colors.error : colors.textSecondary + '40',
                  },
                ]}
                editable={!isRegistering}
                keyboardType="email-address"
                autoCapitalize="none"
                autoComplete="email"
                textContentType="emailAddress"
                returnKeyType="next"
                accessibilityLabel="Email"
                accessibilityHint="Enter your email address"
              />
              {errors.email && (
                <Text
                  style={[
                    styles.errorText,
                    {
                      fontFamily: typography.fontFamily.body,
                      color: colors.error,
                    },
                  ]}
                >
                  {errors.email}
                </Text>
              )}
            </View>

            {/* Phone */}
            <View style={styles.inputGroup}>
              <Text
                style={[
                  styles.label,
                  {
                    fontFamily: typography.fontFamily.bodyBold,
                    color: colors.textPrimary,
                  },
                ]}
              >
                Phone *
              </Text>
              <TextInput
                value={formData.phone}
                onChangeText={(value) => handleInputChange('phone', value)}
                placeholder="+919876543210"
                placeholderTextColor={colors.textSecondary + '80'}
                style={[
                  styles.input,
                  {
                    fontFamily: typography.fontFamily.body,
                    color: colors.textPrimary,
                    backgroundColor: colors.black,
                    borderColor: errors.phone ? colors.error : colors.textSecondary + '40',
                  },
                ]}
                editable={!isRegistering}
                keyboardType="phone-pad"
                autoComplete="tel"
                textContentType="telephoneNumber"
                returnKeyType="next"
                accessibilityLabel="Phone"
                accessibilityHint="Enter your phone number with country code"
              />
              {errors.phone && (
                <Text
                  style={[
                    styles.errorText,
                    {
                      fontFamily: typography.fontFamily.body,
                      color: colors.error,
                    },
                  ]}
                >
                  {errors.phone}
                </Text>
              )}
            </View>

            {/* Business Name (Optional) */}
            <View style={styles.inputGroup}>
              <Text
                style={[
                  styles.label,
                  {
                    fontFamily: typography.fontFamily.bodyBold,
                    color: colors.textPrimary,
                  },
                ]}
              >
                Business Name (Optional)
              </Text>
              <TextInput
                value={formData.businessName}
                onChangeText={(value) => handleInputChange('businessName', value)}
                placeholder="ACME Inc."
                placeholderTextColor={colors.textSecondary + '80'}
                style={[
                  styles.input,
                  {
                    fontFamily: typography.fontFamily.body,
                    color: colors.textPrimary,
                    backgroundColor: colors.black,
                    borderColor: colors.textSecondary + '40',
                  },
                ]}
                editable={!isRegistering}
                autoCapitalize="words"
                autoComplete="organization"
                textContentType="organizationName"
                returnKeyType="done"
                onSubmitEditing={handleSignUp}
                accessibilityLabel="Business Name"
                accessibilityHint="Enter your business name (optional)"
              />
            </View>

            {/* General Error */}
            {generalError && (
              <View style={[styles.errorContainer, { backgroundColor: colors.error + '20' }]}>
                <Text
                  style={[
                    styles.generalError,
                    {
                      fontFamily: typography.fontFamily.body,
                      color: colors.error,
                    },
                  ]}
                >
                  {generalError}
                </Text>
              </View>
            )}

            {/* Sign Up Button */}
            <TouchableOpacity
              onPress={handleSignUp}
              disabled={isRegistering}
              style={[
                styles.signUpButton,
                {
                  backgroundColor: colors.neonCyan,
                  marginTop: spacing.lg,
                },
              ]}
              accessibilityLabel="Sign up"
              accessibilityRole="button"
              accessibilityState={{ disabled: isRegistering }}
            >
              {isRegistering ? (
                <ActivityIndicator color={colors.black} size="small" />
              ) : (
                <Text
                  style={[
                    styles.signUpButtonText,
                    {
                      fontFamily: typography.fontFamily.bodyBold,
                      color: colors.black,
                    },
                  ]}
                >
                  Sign Up
                </Text>
              )}
            </TouchableOpacity>

            {/* Sign In Link */}
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
                Already have an account?{' '}
              </Text>
              <TouchableOpacity
                onPress={onSignInPress}
                disabled={isRegistering}
                accessibilityLabel="Sign in"
                accessibilityRole="button"
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
                  Sign in
                </Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Tagline */}
          <Text
            style={[
              styles.tagline,
              {
                fontFamily: typography.fontFamily.body,
                color: colors.textSecondary,
                marginTop: spacing.xl,
                marginBottom: spacing.xl,
              },
            ]}
          >
            The First AI Agent Marketplace
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
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
    fontSize: 32,
    fontWeight: '700',
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
  },
  form: {
    width: '100%',
  },
  inputGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 14,
    marginBottom: 8,
  },
  input: {
    height: 56,
    borderWidth: 2,
    borderRadius: 12,
    paddingHorizontal: 16,
    fontSize: 16,
  },
  errorText: {
    fontSize: 12,
    marginTop: 4,
  },
  errorContainer: {
    padding: 12,
    borderRadius: 8,
    marginTop: 8,
  },
  generalError: {
    fontSize: 14,
    textAlign: 'center',
  },
  signUpButton: {
    height: 56,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  signUpButtonText: {
    fontSize: 16,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
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
