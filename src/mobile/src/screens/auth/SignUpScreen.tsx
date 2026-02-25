/**
 * Sign Up Screen
 * Customer registration with full form parity with CP web AuthPanel.
 * Implements Stories 1, 2, 3 of mobile iteration 1:
 *   - Story 1: SafeAreaView with all four edges
 *   - Story 2: WAOOAW logo image
 *   - Story 3: Full signup form (11 fields, CP parity)
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
  Modal,
} from 'react-native';
import { Image } from 'expo-image';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '../../hooks/useTheme';
import RegistrationService, {
  RegistrationServiceError,
  RegistrationErrorCode,
} from '../../services/registration.service';

// ─── Constants ────────────────────────────────────────────────────────────────

const BUSINESS_INDUSTRY_OPTIONS = [
  'Marketing',
  'Education',
  'Sales',
  'Technology',
  'Healthcare',
  'Finance',
  'Retail',
  'Real Estate',
  'Other',
];

const PHONE_COUNTRY_OPTIONS: Array<{ code: string; label: string; dialCode: string }> = [
  { code: 'IN', label: 'India', dialCode: '+91' },
  { code: 'US', label: 'United States', dialCode: '+1' },
  { code: 'GB', label: 'United Kingdom', dialCode: '+44' },
  { code: 'AE', label: 'UAE', dialCode: '+971' },
  { code: 'SG', label: 'Singapore', dialCode: '+65' },
  { code: 'AU', label: 'Australia', dialCode: '+61' },
  { code: 'CA', label: 'Canada', dialCode: '+1' },
];

const GSTIN_REGEX = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/;
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const URL_REGEX = /^https?:\/\/.+\..+/;

// ─── Types ────────────────────────────────────────────────────────────────────

export interface SignUpScreenProps {
  /** Callback when user wants to sign in instead */
  onSignInPress?: () => void;
  /** Callback when registration is successful (before OTP) */
  onRegistrationSuccess?: (
    registrationId: string,
    otpId: string,
    channel: string,
    destinationMasked: string,
  ) => void;
}

interface FormData {
  fullName: string;
  businessName: string;
  businessIndustry: string;
  businessAddress: string;
  email: string;
  phoneCountry: string;
  phoneNationalNumber: string;
  website: string;
  gstNumber: string;
  preferredContactMethod: 'email' | 'phone' | '';
  consent: boolean;
}

type FormErrors = Partial<Record<keyof FormData, string>>;

// ─── ModalPicker ──────────────────────────────────────────────────────────────

interface ModalPickerProps {
  visible: boolean;
  title: string;
  options: string[];
  selectedValue: string;
  onSelect: (value: string) => void;
  onClose: () => void;
  colors: ReturnType<typeof useTheme>['colors'];
}

const ModalPicker: React.FC<ModalPickerProps> = ({
  visible,
  title,
  options,
  selectedValue,
  onSelect,
  onClose,
  colors,
}) => (
  <Modal
    visible={visible}
    transparent
    animationType="slide"
    onRequestClose={onClose}
    accessibilityViewIsModal
  >
    <TouchableOpacity
      style={pickerStyles.overlay}
      activeOpacity={1}
      onPress={onClose}
    >
      <View style={[pickerStyles.sheet, { backgroundColor: colors.gray900 }]}>
        <View style={[pickerStyles.header, { borderBottomColor: colors.textSecondary + '30' }]}>
          <Text style={[pickerStyles.title, { color: colors.textPrimary }]}>{title}</Text>
          <TouchableOpacity onPress={onClose} accessibilityLabel="Close picker">
            <Text style={[pickerStyles.close, { color: colors.neonCyan }]}>Done</Text>
          </TouchableOpacity>
        </View>
        <ScrollView>
          {options.map((opt) => (
            <TouchableOpacity
              key={opt}
              style={[
                pickerStyles.option,
                opt === selectedValue && { backgroundColor: colors.neonCyan + '20' },
              ]}
              onPress={() => { onSelect(opt); onClose(); }}
              accessibilityLabel={opt}
            >
              <Text style={[
                pickerStyles.optionText,
                { color: opt === selectedValue ? colors.neonCyan : colors.textPrimary },
              ]}>
                {opt}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>
    </TouchableOpacity>
  </Modal>
);

const pickerStyles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'flex-end',
  },
  sheet: {
    maxHeight: '60%' as any,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    overflow: 'hidden',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
  },
  close: {
    fontSize: 16,
    fontWeight: '600',
  },
  option: {
    paddingVertical: 14,
    paddingHorizontal: 20,
  },
  optionText: {
    fontSize: 16,
  },
});

// ─── CountryPicker ────────────────────────────────────────────────────────────

interface CountryPickerProps {
  visible: boolean;
  selectedCode: string;
  onSelect: (code: string) => void;
  onClose: () => void;
  colors: ReturnType<typeof useTheme>['colors'];
}

const CountryPicker: React.FC<CountryPickerProps> = ({
  visible,
  selectedCode,
  onSelect,
  onClose,
  colors,
}) => (
  <Modal
    visible={visible}
    transparent
    animationType="slide"
    onRequestClose={onClose}
    accessibilityViewIsModal
  >
    <TouchableOpacity
      style={pickerStyles.overlay}
      activeOpacity={1}
      onPress={onClose}
    >
      <View style={[pickerStyles.sheet, { backgroundColor: colors.gray900 }]}>
        <View style={[pickerStyles.header, { borderBottomColor: colors.textSecondary + '30' }]}>
          <Text style={[pickerStyles.title, { color: colors.textPrimary }]}>Select Country</Text>
          <TouchableOpacity onPress={onClose} accessibilityLabel="Close country picker">
            <Text style={[pickerStyles.close, { color: colors.neonCyan }]}>Done</Text>
          </TouchableOpacity>
        </View>
        <ScrollView>
          {PHONE_COUNTRY_OPTIONS.map((c) => (
            <TouchableOpacity
              key={c.code}
              style={[
                pickerStyles.option,
                c.code === selectedCode && { backgroundColor: colors.neonCyan + '20' },
              ]}
              onPress={() => { onSelect(c.code); onClose(); }}
              accessibilityLabel={`${c.label} ${c.dialCode}`}
            >
              <Text style={[
                pickerStyles.optionText,
                { color: c.code === selectedCode ? colors.neonCyan : colors.textPrimary },
              ]}>
                {c.label}  <Text style={{ opacity: 0.6 }}>{c.dialCode}</Text>
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>
    </TouchableOpacity>
  </Modal>
);

// ─── SignUpScreen ──────────────────────────────────────────────────────────────

export const SignUpScreen: React.FC<SignUpScreenProps> = ({
  onSignInPress,
  onRegistrationSuccess,
}) => {
  const { colors, spacing, typography } = useTheme();

  // Form state
  const [formData, setFormData] = useState<FormData>({
    fullName: '',
    businessName: '',
    businessIndustry: '',
    businessAddress: '',
    email: '',
    phoneCountry: 'IN',
    phoneNationalNumber: '',
    website: '',
    gstNumber: '',
    preferredContactMethod: '',
    consent: false,
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [isRegistering, setIsRegistering] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);

  // Picker visibility
  const [industryPickerVisible, setIndustryPickerVisible] = useState(false);
  const [countryPickerVisible, setCountryPickerVisible] = useState(false);

  // ── Helpers ──────────────────────────────────────────────────────────────────

  const selectedCountry = PHONE_COUNTRY_OPTIONS.find(
    (c) => c.code === formData.phoneCountry
  ) ?? PHONE_COUNTRY_OPTIONS[0];

  const handleChange = <K extends keyof FormData>(field: K, value: FormData[K]) => {
    setFormData((prev) => ({ ...prev, [field]: value }));

    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }

    if (generalError) setGeneralError(null);
  };

  // ── Validation ───────────────────────────────────────────────────────────────

  const validateForm = (): boolean => {
    const e: FormErrors = {};

    if (!formData.fullName.trim()) {
      e.fullName = 'Full name is required';
    } else if (formData.fullName.trim().length < 2) {
      e.fullName = 'Name must be at least 2 characters';
    }

    if (!formData.businessName.trim()) {
      e.businessName = 'Business name is required';
    }

    if (!formData.businessIndustry) {
      e.businessIndustry = 'Business industry is required';
    }

    if (!formData.businessAddress.trim()) {
      e.businessAddress = 'Business address is required';
    }

    if (!formData.email.trim()) {
      e.email = 'Email is required';
    } else if (!EMAIL_REGEX.test(formData.email)) {
      e.email = 'Invalid email format';
    }

    if (!formData.phoneNationalNumber.trim()) {
      e.phoneNationalNumber = 'Phone number is required';
    } else if (formData.phoneCountry === 'IN') {
      if (!/^[6-9]\d{9}$/.test(formData.phoneNationalNumber.trim())) {
        e.phoneNationalNumber = 'Enter a valid 10-digit Indian mobile number';
      }
    } else {
      if (!/^\d{6,12}$/.test(formData.phoneNationalNumber.trim())) {
        e.phoneNationalNumber = 'Enter a valid phone number (6–12 digits)';
      }
    }

    if (formData.website.trim() && !URL_REGEX.test(formData.website.trim())) {
      e.website = 'Enter a valid URL (e.g. https://example.com)';
    }

    if (formData.gstNumber.trim() && !GSTIN_REGEX.test(formData.gstNumber.trim().toUpperCase())) {
      e.gstNumber = 'Enter a valid GSTIN (e.g. 22AAAAA0000A1Z5)';
    }

    if (!formData.preferredContactMethod) {
      e.preferredContactMethod = 'Select a preferred contact method';
    }

    if (!formData.consent) {
      e.consent = 'You must accept the terms to continue';
    }

    setErrors(e);
    return Object.keys(e).length === 0;
  };

  // ── Submit ───────────────────────────────────────────────────────────────────

  const handleSignUp = async () => {
    if (!validateForm()) return;

    setIsRegistering(true);
    setGeneralError(null);

    try {
      const result = await RegistrationService.registerAndStartOTP({
        fullName: formData.fullName.trim(),
        email: formData.email.trim().toLowerCase(),
        phoneCountry: formData.phoneCountry,
        phoneNationalNumber: formData.phoneNationalNumber.trim(),
        businessName: formData.businessName.trim(),
        businessIndustry: formData.businessIndustry,
        businessAddress: formData.businessAddress.trim(),
        website: formData.website.trim() || undefined,
        gstNumber: formData.gstNumber.trim() || undefined,
        preferredContactMethod: formData.preferredContactMethod as 'email' | 'phone',
        consent: formData.consent,
      });

      if (!result?.registration || !result?.otp) return;

      const { registration, otp } = result;

      if (onRegistrationSuccess) {
        onRegistrationSuccess(
          registration.registration_id,
          otp.otp_id,
          otp.channel,
          otp.destination_masked,
        );
      }
    } catch (error: any) {
      const errorCode = error?.code;
      const isServiceError =
        typeof RegistrationServiceError === 'function' && error instanceof RegistrationServiceError;

      if (isServiceError || typeof errorCode === 'string') {
        switch (errorCode) {
          case RegistrationErrorCode.EMAIL_ALREADY_REGISTERED:
          case 'EMAIL_ALREADY_REGISTERED':
            setErrors({ email: 'Email already registered' });
            setGeneralError('This email is already registered. Please sign in.');
            break;
          case RegistrationErrorCode.PHONE_ALREADY_REGISTERED:
          case 'PHONE_ALREADY_REGISTERED':
            setErrors({ phoneNationalNumber: 'Phone already registered' });
            setGeneralError('This phone is already registered. Please sign in.');
            break;
          default:
            setGeneralError(error.message || 'Registration failed. Please try again.');
        }
      } else {
        setGeneralError('Registration failed. Please try again.');
      }
    } finally {
      setIsRegistering(false);
    }
  };

  // ── Render helpers ────────────────────────────────────────────────────────────

  const inputStyle = (hasError: boolean): object => ({
    color: colors.textPrimary,
    backgroundColor: colors.black,
    borderColor: hasError ? colors.error : colors.textSecondary + '40',
    fontFamily: typography.fontFamily.body,
  });

  const renderLabel = (text: string) => (
    <Text
      style={[
        styles.label,
        { fontFamily: typography.fontFamily.bodyBold, color: colors.textPrimary },
      ]}
    >
      {text}
    </Text>
  );

  const renderError = (field: keyof FormErrors) =>
    errors[field] ? (
      <Text
        style={[styles.errorText, { color: colors.error, fontFamily: typography.fontFamily.body }]}
      >
        {errors[field]}
      </Text>
    ) : null;

  // ── Render ────────────────────────────────────────────────────────────────────

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: colors.black }]}
      edges={['top', 'bottom', 'left', 'right']}
    >
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView
          contentContainerStyle={[
            styles.scrollContent,
            { paddingHorizontal: spacing.screenPadding.horizontal },
          ]}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* Header */}
          <View style={[styles.header, { marginTop: spacing.xl }]}>
            <Image
              source={require('../../../assets/WAOOAW Logo.png')}
              style={styles.logoImage}
              contentFit="contain"
              accessibilityLabel="WAOOAW"
            />
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

            {/* ── Full Name ── */}
            <View style={styles.inputGroup}>
              {renderLabel('Full Name *')}
              <TextInput
                value={formData.fullName}
                onChangeText={(v) => handleChange('fullName', v)}
                placeholder="John Doe"
                placeholderTextColor={colors.textSecondary + '80'}
                style={[styles.input, inputStyle(!!errors.fullName)]}
                editable={!isRegistering}
                autoCapitalize="words"
                autoComplete="name"
                textContentType="name"
                returnKeyType="next"
                accessibilityLabel="Full Name"
                accessibilityHint="Enter your full name"
              />
              {renderError('fullName')}
            </View>

            {/* ── Business Name ── */}
            <View style={styles.inputGroup}>
              {renderLabel('Business Name *')}
              <TextInput
                value={formData.businessName}
                onChangeText={(v) => handleChange('businessName', v)}
                placeholder="ACME Inc."
                placeholderTextColor={colors.textSecondary + '80'}
                style={[styles.input, inputStyle(!!errors.businessName)]}
                editable={!isRegistering}
                autoCapitalize="words"
                autoComplete="organization"
                textContentType="organizationName"
                returnKeyType="next"
                accessibilityLabel="Business Name"
                accessibilityHint="Enter your business name"
              />
              {renderError('businessName')}
            </View>

            {/* ── Business Industry ── */}
            <View style={styles.inputGroup}>
              {renderLabel('Business Industry *')}
              <TouchableOpacity
                onPress={() => !isRegistering && setIndustryPickerVisible(true)}
                style={[
                  styles.input,
                  styles.pickerButton,
                  {
                    backgroundColor: colors.black,
                    borderColor: errors.businessIndustry
                      ? colors.error
                      : colors.textSecondary + '40',
                  },
                ]}
                accessibilityLabel="Business Industry"
                accessibilityHint="Tap to select your industry"
                accessibilityRole="button"
              >
                <Text
                  style={[
                    styles.pickerText,
                    {
                      fontFamily: typography.fontFamily.body,
                      color: formData.businessIndustry
                        ? colors.textPrimary
                        : colors.textSecondary + '80',
                    },
                  ]}
                >
                  {formData.businessIndustry || 'Select industry'}
                </Text>
                <Text style={{ color: colors.textSecondary, fontSize: 12 }}>▼</Text>
              </TouchableOpacity>
              {renderError('businessIndustry')}
            </View>

            {/* ── Business Address ── */}
            <View style={styles.inputGroup}>
              {renderLabel('Business Address *')}
              <TextInput
                value={formData.businessAddress}
                onChangeText={(v) => handleChange('businessAddress', v)}
                placeholder="123 Main Street, City"
                placeholderTextColor={colors.textSecondary + '80'}
                style={[styles.input, inputStyle(!!errors.businessAddress)]}
                editable={!isRegistering}
                autoCapitalize="words"
                autoComplete="street-address"
                textContentType="streetAddressLine1"
                returnKeyType="next"
                accessibilityLabel="Business Address"
                accessibilityHint="Enter your business address"
              />
              {renderError('businessAddress')}
            </View>

            {/* ── Email ── */}
            <View style={styles.inputGroup}>
              {renderLabel('Email *')}
              <TextInput
                value={formData.email}
                onChangeText={(v) => handleChange('email', v)}
                placeholder="john@example.com"
                placeholderTextColor={colors.textSecondary + '80'}
                style={[styles.input, inputStyle(!!errors.email)]}
                editable={!isRegistering}
                keyboardType="email-address"
                autoCapitalize="none"
                autoComplete="email"
                textContentType="emailAddress"
                returnKeyType="next"
                accessibilityLabel="Email"
                accessibilityHint="Enter your email address"
              />
              {renderError('email')}
            </View>

            {/* ── Phone: Country + Number ── */}
            <View style={styles.inputGroup}>
              {renderLabel('Phone *')}
              <View style={styles.phoneRow}>
                <TouchableOpacity
                  onPress={() => !isRegistering && setCountryPickerVisible(true)}
                  style={[
                    styles.countryButton,
                    {
                      backgroundColor: colors.black,
                      borderColor: errors.phoneNationalNumber
                        ? colors.error
                        : colors.textSecondary + '40',
                    },
                  ]}
                  accessibilityLabel={`Country code ${selectedCountry.dialCode}`}
                  accessibilityHint="Tap to change country code"
                  accessibilityRole="button"
                >
                  <Text
                    style={[
                      styles.countryCode,
                      { color: colors.textPrimary, fontFamily: typography.fontFamily.body },
                    ]}
                  >
                    {selectedCountry.dialCode}
                  </Text>
                  <Text style={{ color: colors.textSecondary, fontSize: 10 }}>▼</Text>
                </TouchableOpacity>

                <TextInput
                  value={formData.phoneNationalNumber}
                  onChangeText={(v) => handleChange('phoneNationalNumber', v.replace(/\D/g, ''))}
                  placeholder={formData.phoneCountry === 'IN' ? '9876543210' : '555123456'}
                  placeholderTextColor={colors.textSecondary + '80'}
                  style={[styles.input, styles.phoneInput, inputStyle(!!errors.phoneNationalNumber)]}
                  editable={!isRegistering}
                  keyboardType="number-pad"
                  autoComplete="tel"
                  textContentType="telephoneNumber"
                  returnKeyType="next"
                  accessibilityLabel="Phone Number"
                  accessibilityHint="Enter your phone number without country code"
                  maxLength={formData.phoneCountry === 'IN' ? 10 : 12}
                />
              </View>
              {renderError('phoneNationalNumber')}
            </View>

            {/* ── Website (optional) ── */}
            <View style={styles.inputGroup}>
              {renderLabel('Website (Optional)')}
              <TextInput
                value={formData.website}
                onChangeText={(v) => handleChange('website', v)}
                placeholder="https://yourcompany.com"
                placeholderTextColor={colors.textSecondary + '80'}
                style={[styles.input, inputStyle(!!errors.website)]}
                editable={!isRegistering}
                keyboardType="url"
                autoCapitalize="none"
                autoComplete="url"
                textContentType="URL"
                returnKeyType="next"
                accessibilityLabel="Website"
                accessibilityHint="Enter your company website (optional)"
              />
              {renderError('website')}
            </View>

            {/* ── GST Number (optional) ── */}
            <View style={styles.inputGroup}>
              {renderLabel('GST Number (Optional)')}
              <TextInput
                value={formData.gstNumber}
                onChangeText={(v) => handleChange('gstNumber', v.toUpperCase())}
                placeholder="22AAAAA0000A1Z5"
                placeholderTextColor={colors.textSecondary + '80'}
                style={[styles.input, inputStyle(!!errors.gstNumber)]}
                editable={!isRegistering}
                autoCapitalize="characters"
                returnKeyType="next"
                accessibilityLabel="GST Number"
                accessibilityHint="Enter your GSTIN (optional)"
                maxLength={15}
              />
              {renderError('gstNumber')}
            </View>

            {/* ── Preferred Contact Method ── */}
            <View style={styles.inputGroup}>
              {renderLabel('Preferred Contact Method *')}
              <View style={styles.toggleRow}>
                <TouchableOpacity
                  onPress={() => handleChange('preferredContactMethod', 'email')}
                  disabled={isRegistering}
                  style={[
                    styles.toggleButton,
                    {
                      backgroundColor:
                        formData.preferredContactMethod === 'email'
                          ? colors.neonCyan
                          : colors.black,
                      borderColor:
                        errors.preferredContactMethod
                          ? colors.error
                          : formData.preferredContactMethod === 'email'
                          ? colors.neonCyan
                          : colors.textSecondary + '40',
                    },
                  ]}
                  accessibilityLabel="Email contact method"
                  accessibilityRole="radio"
                  accessibilityState={{ selected: formData.preferredContactMethod === 'email' }}
                >
                  <Text
                    style={[
                      styles.toggleText,
                      {
                        fontFamily: typography.fontFamily.bodyBold,
                        color:
                          formData.preferredContactMethod === 'email'
                            ? colors.black
                            : colors.textPrimary,
                      },
                    ]}
                  >
                    Email
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  onPress={() => handleChange('preferredContactMethod', 'phone')}
                  disabled={isRegistering}
                  style={[
                    styles.toggleButton,
                    {
                      backgroundColor:
                        formData.preferredContactMethod === 'phone'
                          ? colors.neonCyan
                          : colors.black,
                      borderColor:
                        errors.preferredContactMethod
                          ? colors.error
                          : formData.preferredContactMethod === 'phone'
                          ? colors.neonCyan
                          : colors.textSecondary + '40',
                      marginLeft: 12,
                    },
                  ]}
                  accessibilityLabel="Phone contact method"
                  accessibilityRole="radio"
                  accessibilityState={{ selected: formData.preferredContactMethod === 'phone' }}
                >
                  <Text
                    style={[
                      styles.toggleText,
                      {
                        fontFamily: typography.fontFamily.bodyBold,
                        color:
                          formData.preferredContactMethod === 'phone'
                            ? colors.black
                            : colors.textPrimary,
                      },
                    ]}
                  >
                    Phone
                  </Text>
                </TouchableOpacity>
              </View>
              {renderError('preferredContactMethod')}
            </View>

            {/* ── Consent ── */}
            <View style={styles.inputGroup}>
              <TouchableOpacity
                onPress={() => handleChange('consent', !formData.consent)}
                disabled={isRegistering}
                style={styles.consentRow}
                accessibilityLabel="I agree to the Terms of Service and Privacy Policy"
                accessibilityRole="checkbox"
                accessibilityState={{ checked: formData.consent }}
              >
                <View
                  style={[
                    styles.checkbox,
                    {
                      backgroundColor: formData.consent ? colors.neonCyan : 'transparent',
                      borderColor: errors.consent
                        ? colors.error
                        : formData.consent
                        ? colors.neonCyan
                        : colors.textSecondary + '60',
                    },
                  ]}
                >
                  {formData.consent && (
                    <Text style={{ color: colors.black, fontSize: 12, fontWeight: '700' }}>✓</Text>
                  )}
                </View>
                <Text
                  style={[
                    styles.consentText,
                    { fontFamily: typography.fontFamily.body, color: colors.textSecondary },
                  ]}
                >
                  I agree to the{' '}
                  <Text style={{ color: colors.neonCyan }}>Terms of Service</Text>
                  {' '}and{' '}
                  <Text style={{ color: colors.neonCyan }}>Privacy Policy</Text>
                </Text>
              </TouchableOpacity>
              {renderError('consent')}
            </View>

            {/* ── General Error ── */}
            {generalError && (
              <View style={[styles.errorContainer, { backgroundColor: colors.error + '20' }]}>
                <Text
                  style={[
                    styles.generalError,
                    { fontFamily: typography.fontFamily.body, color: colors.error },
                  ]}
                >
                  {generalError}
                </Text>
              </View>
            )}

            {/* ── Sign Up Button ── */}
            <TouchableOpacity
              onPress={handleSignUp}
              disabled={isRegistering}
              style={[
                styles.signUpButton,
                { backgroundColor: colors.neonCyan, marginTop: spacing.lg },
              ]}
              accessibilityLabel="Sign up"
              accessibilityRole="button"
              accessibilityState={{ disabled: isRegistering }}
            >
              {isRegistering && (
                <ActivityIndicator
                  color={colors.black}
                  size="small"
                  style={{ marginRight: spacing.xs }}
                />
              )}
              <Text
                style={[
                  styles.signUpButtonText,
                  { fontFamily: typography.fontFamily.bodyBold, color: colors.black },
                ]}
              >
                Sign Up
              </Text>
            </TouchableOpacity>

            {/* ── Sign In Link ── */}
            <View style={[styles.footer, { marginTop: spacing.xl }]}>
              <Text
                style={[
                  styles.footerText,
                  { fontFamily: typography.fontFamily.body, color: colors.textSecondary },
                ]}
              >
                Already have an account?{' '}
              </Text>
              <TouchableOpacity
                onPress={() => { if (!isRegistering) onSignInPress?.(); }}
                disabled={isRegistering}
                accessibilityLabel="Sign in"
                accessibilityRole="button"
              >
                <Text
                  style={[
                    styles.footerLink,
                    { fontFamily: typography.fontFamily.bodyBold, color: colors.neonCyan },
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

      {/* Pickers */}
      <ModalPicker
        visible={industryPickerVisible}
        title="Business Industry"
        options={BUSINESS_INDUSTRY_OPTIONS}
        selectedValue={formData.businessIndustry}
        onSelect={(v) => handleChange('businessIndustry', v)}
        onClose={() => setIndustryPickerVisible(false)}
        colors={colors}
      />

      <CountryPicker
        visible={countryPickerVisible}
        selectedCode={formData.phoneCountry}
        onSelect={(code) => {
          handleChange('phoneCountry', code);
          handleChange('phoneNationalNumber', '');
        }}
        onClose={() => setCountryPickerVisible(false)}
        colors={colors}
      />
    </SafeAreaView>
  );
};

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: { flex: 1 },
  keyboardView: { flex: 1 },
  scrollContent: { flexGrow: 1 },
  header: { alignItems: 'center' },
  logoImage: { width: 180, height: 60 },
  title: { fontSize: 32, fontWeight: '700' },
  subtitle: { fontSize: 16, textAlign: 'center' },
  form: { width: '100%' },
  inputGroup: { marginBottom: 20 },
  label: { fontSize: 14, marginBottom: 8 },
  input: {
    height: 56,
    borderWidth: 2,
    borderRadius: 12,
    paddingHorizontal: 16,
    fontSize: 16,
  },
  pickerButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  pickerText: { fontSize: 16 },
  phoneRow: { flexDirection: 'row', alignItems: 'center' },
  countryButton: {
    height: 56,
    borderWidth: 2,
    borderRadius: 12,
    paddingHorizontal: 12,
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 10,
    minWidth: 80,
  },
  countryCode: { fontSize: 15, marginRight: 4 },
  phoneInput: { flex: 1 },
  toggleRow: { flexDirection: 'row' },
  toggleButton: {
    flex: 1,
    height: 48,
    borderWidth: 2,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  toggleText: { fontSize: 15 },
  consentRow: { flexDirection: 'row', alignItems: 'flex-start' },
  checkbox: {
    width: 22,
    height: 22,
    borderWidth: 2,
    borderRadius: 4,
    marginRight: 10,
    marginTop: 2,
    justifyContent: 'center',
    alignItems: 'center',
  },
  consentText: { fontSize: 14, flex: 1, lineHeight: 20 },
  errorText: { fontSize: 12, marginTop: 4 },
  errorContainer: { padding: 12, borderRadius: 8, marginTop: 8 },
  generalError: { fontSize: 14, textAlign: 'center' },
  signUpButton: {
    height: 56,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    flexDirection: 'row',
  },
  signUpButtonText: { fontSize: 16 },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  footerText: { fontSize: 14 },
  footerLink: { fontSize: 14 },
  tagline: { fontSize: 12, textAlign: 'center', opacity: 0.6 },
});
