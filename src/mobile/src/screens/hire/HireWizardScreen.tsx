/**
 * Hire Wizard Screen - Multi-step agent hiring flow
 * 
 * Steps:
 * 1. Confirm Agent Selection
 * 2. Trial Details (start date, goals)
 * 3. Payment Details (Razorpay)
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  SafeAreaView,
  TouchableOpacity,
  TextInput,
} from 'react-native';
import { useRoute, useNavigation, RouteProp } from '@react-navigation/native';
import { useTheme } from '@/hooks/useTheme';
import { useAgentDetail } from '@/hooks/useAgentDetail';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { ErrorView } from '@/components/ErrorView';

// Navigation types
type HireWizardParams = {
  agentId: string;
};
type HireWizardRouteProp = RouteProp<{ HireWizard: HireWizardParams }, 'HireWizard'>;

// Step components
const Step1ConfirmAgent = ({ agent, onNext, onCancel }: any) => {
  const { colors, spacing } = useTheme();

  return (
    <View style={{ padding: spacing.lg }}>
      <Text style={[styles.stepTitle, { color: colors.textPrimary }]}>
        Confirm Agent Selection
      </Text>

      {/* Agent Summary Card */}
      <View style={[styles.agentCard, { backgroundColor: colors.card }]}>
        {/* Avatar */}
        <View style={[styles.avatar, { backgroundColor: colors.neonCyan }]}>
          <Text style={[styles.avatarText, { color: colors.black }]}>
            {agent.name.charAt(0).toUpperCase()}
          </Text>
        </View>

        {/* Agent Info */}
        <Text style={[styles.agentName, { color: colors.textPrimary }]}>
          {agent.name}
        </Text>
        <Text style={[styles.agentSpecialty, { color: colors.neonCyan }]}>
          {agent.specialization}
        </Text>

        {/* Industry Badge */}
        <View style={styles.badgeContainer}>
          <View style={[styles.badge, { backgroundColor: `${colors.neonCyan}22` }]}>
            <Text style={{ color: colors.textSecondary, fontSize: 12 }}>
              {agent.industry}
            </Text>
          </View>
        </View>

        {/* Pricing */}
        {agent.price && (
          <View style={styles.pricingSection}>
            <Text style={[styles.priceLabel, { color: colors.textSecondary }]}>
              Monthly Rate
            </Text>
            <Text style={[styles.price, { color: colors.textPrimary }]}>
              ₹{agent.price.toLocaleString('en-IN')}
            </Text>
          </View>
        )}

        {/* Trial Info */}
        <View style={[styles.trialBanner, { backgroundColor: `${colors.neonCyan}11` }]}>
          <Text style={[styles.trialText, { color: colors.neonCyan }]}>
            🎁 Start with a {agent.trial_days || 7}-day free trial
          </Text>
          <Text style={[styles.trialSubtext, { color: colors.textSecondary }]}>
            Try risk-free. Keep all deliverables even if you don't hire.
          </Text>
        </View>
      </View>

      {/* What Happens Next */}
      <View style={{ marginTop: spacing.lg }}>
        <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>
          What happens next?
        </Text>
        <View style={{ marginTop: spacing.sm }}>
          {[
            '1. Configure your trial period and goals',
            '2. Add payment method (no charge during trial)',
            '3. Agent starts working immediately',
            '4. Review deliverables and decide to hire or cancel',
          ].map((step, index) => (
            <Text
              key={index}
              style={[styles.stepItem, { color: colors.textSecondary, marginBottom: spacing.xs }]}
            >
              {step}
            </Text>
          ))}
        </View>
      </View>

      {/* Action Buttons */}
      <View style={{ marginTop: spacing.xl }}>
        <TouchableOpacity
          style={[styles.primaryButton, { backgroundColor: colors.neonCyan }]}
          onPress={onNext}
        >
          <Text style={[styles.primaryButtonText, { color: colors.black }]}>
            Continue to Trial Details
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.secondaryButton, { marginTop: spacing.md }]}
          onPress={onCancel}
        >
          <Text style={[styles.secondaryButtonText, { color: colors.textSecondary }]}>
            Cancel
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const Step2TrialDetails = ({ 
  trialData, 
  onTrialDataChange, 
  onNext, 
  onBack 
}: { 
  trialData: any; 
  onTrialDataChange: (field: string, value: string) => void; 
  onNext: () => void; 
  onBack: () => void;
}) => {
  const { colors, spacing } = useTheme();
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!trialData.startDate || trialData.startDate.trim() === '') {
      newErrors.startDate = 'Start date is required';
    }

    if (!trialData.goals || trialData.goals.trim() === '') {
      newErrors.goals = 'Trial goals are required';
    } else if (trialData.goals.length < 10) {
      newErrors.goals = 'Please provide more detailed goals (at least 10 characters)';
    }

    if (!trialData.deliverables || trialData.deliverables.trim() === '') {
      newErrors.deliverables = 'Expected deliverables are required';
    } else if (trialData.deliverables.length < 10) {
      newErrors.deliverables = 'Please provide more details (at least 10 characters)';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateForm()) {
      onNext();
    }
  };

  return (
    <View style={{ padding: spacing.lg }}>
      <Text style={[styles.stepTitle, { color: colors.textPrimary }]}>
        Trial Details
      </Text>
      <Text style={[styles.stepSubtitle, { color: colors.textSecondary, marginTop: spacing.sm }]}>
        Configure your 7-day trial period
      </Text>

      {/* Form Fields */}
      <View style={{ marginTop: spacing.lg }}>
        {/* Start Date */}
        <View style={{ marginBottom: spacing.lg }}>
          <Text style={[styles.fieldLabel, { color: colors.textPrimary }]}>
            Start Date *
          </Text>
          <TextInput
            style={[
              styles.textInput,
              {
                backgroundColor: colors.card,
                color: colors.textPrimary,
                borderColor: errors.startDate ? '#ef4444' : colors.textSecondary + '40',
                borderWidth: 1,
              },
            ]}
            placeholder="YYYY-MM-DD (e.g., 2026-02-20)"
            placeholderTextColor={colors.textSecondary}
            value={trialData.startDate}
            onChangeText={(text) => {
              onTrialDataChange('startDate', text);
              if (errors.startDate) {
                setErrors({ ...errors, startDate: '' });
              }
            }}
          />
          {errors.startDate && (
            <Text style={[styles.errorText, { color: '#ef4444' }]}>
              {errors.startDate}
            </Text>
          )}
          <Text style={[styles.fieldHint, { color: colors.textSecondary }]}>
            When would you like to start the trial? (Format: YYYY-MM-DD)
          </Text>
        </View>

        {/* Trial Goals */}
        <View style={{ marginBottom: spacing.lg }}>
          <Text style={[styles.fieldLabel, { color: colors.textPrimary }]}>
            Trial Goals *
          </Text>
          <TextInput
            style={[
              styles.textArea,
              {
                backgroundColor: colors.card,
                color: colors.textPrimary,
                borderColor: errors.goals ? '#ef4444' : colors.textSecondary + '40',
                borderWidth: 1,
              },
            ]}
            placeholder="What do you want to achieve during the trial?"
            placeholderTextColor={colors.textSecondary}
            value={trialData.goals}
            onChangeText={(text) => {
              onTrialDataChange('goals', text);
              if (errors.goals) {
                setErrors({ ...errors, goals: '' });
              }
            }}
            multiline
            numberOfLines={4}
            textAlignVertical="top"
          />
          {errors.goals && (
            <Text style={[styles.errorText, { color: '#ef4444' }]}>
              {errors.goals}
            </Text>
          )}
          <Text style={[styles.fieldHint, { color: colors.textSecondary }]}>
            Describe your objectives for the 7-day trial period
          </Text>
        </View>

        {/* Expected Deliverables */}
        <View style={{ marginBottom: spacing.lg }}>
          <Text style={[styles.fieldLabel, { color: colors.textPrimary }]}>
            Expected Deliverables *
          </Text>
          <TextInput
            style={[
              styles.textArea,
              {
                backgroundColor: colors.card,
                color: colors.textPrimary,
                borderColor: errors.deliverables ? '#ef4444' : colors.textSecondary + '40',
                borderWidth: 1,
              },
            ]}
            placeholder="What specific deliverables do you expect?"
            placeholderTextColor={colors.textSecondary}
            value={trialData.deliverables}
            onChangeText={(text) => {
              onTrialDataChange('deliverables', text);
              if (errors.deliverables) {
                setErrors({ ...errors, deliverables: '' });
              }
            }}
            multiline
            numberOfLines={4}
            textAlignVertical="top"
          />
          {errors.deliverables && (
            <Text style={[styles.errorText, { color: '#ef4444' }]}>
              {errors.deliverables}
            </Text>
          )}
          <Text style={[styles.fieldHint, { color: colors.textSecondary }]}>
            List the outputs you expect at the end of the trial
          </Text>
        </View>
      </View>

      {/* Action Buttons */}
      <View style={{ marginTop: spacing.xl }}>
        <TouchableOpacity
          style={[styles.primaryButton, { backgroundColor: colors.neonCyan }]}
          onPress={handleNext}
        >
          <Text style={[styles.primaryButtonText, { color: colors.black }]}>
            Continue to Payment
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.secondaryButton, { marginTop: spacing.md }]}
          onPress={onBack}
        >
          <Text style={[styles.secondaryButtonText, { color: colors.textSecondary }]}>
            Back
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const Step3Payment = ({
  agent,
  paymentData,
  onPaymentDataChange,
  onComplete,
  onBack,
}: {
  agent: any;
  paymentData: any;
  onPaymentDataChange: (field: string, value: any) => void;
  onComplete: () => void;
  onBack: () => void;
}) => {
  const { colors, spacing } = useTheme();
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!paymentData.fullName || paymentData.fullName.trim() === '') {
      newErrors.fullName = 'Full name is required';
    }

    if (!paymentData.email || paymentData.email.trim() === '') {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(paymentData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!paymentData.phone || paymentData.phone.trim() === '') {
      newErrors.phone = 'Phone number is required';
    } else if (!/^\d{10}$/.test(paymentData.phone.replace(/[- ]/g, ''))) {
      newErrors.phone = 'Please enter a valid 10-digit phone number';
    }

    if (!paymentData.paymentMethod) {
      newErrors.paymentMethod = 'Please select a payment method';
    }

    if (!paymentData.acceptedTerms) {
      newErrors.acceptedTerms = 'You must accept the terms and conditions';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleComplete = () => {
    if (validateForm()) {
      onComplete();
    }
  };

  return (
    <View style={{ padding: spacing.lg }}>
      <Text style={[styles.stepTitle, { color: colors.textPrimary }]}>
        Payment Details
      </Text>
      <Text style={[styles.stepSubtitle, { color: colors.textSecondary, marginTop: spacing.sm }]}>
        Add a payment method (no charge during trial)
      </Text>

      {/* Pricing Summary */}
      <View style={[styles.pricingSummary, { backgroundColor: colors.card, marginTop: spacing.lg }]}>
        <Text style={[styles.pricingTitle, { color: colors.textPrimary }]}>
          Pricing Summary
        </Text>
        <View style={styles.pricingRow}>
          <Text style={[styles.pricingLabel, { color: colors.textSecondary }]}>
            Monthly Rate
          </Text>
          <Text style={[styles.pricingValue, { color: colors.textPrimary }]}>
            ₹{agent.price.toLocaleString('en-IN')}
          </Text>
        </View>
        <View style={styles.pricingRow}>
          <Text style={[styles.pricingLabel, { color: colors.textSecondary }]}>
            Trial Period
          </Text>
          <Text style={[styles.pricingValue, { color: colors.neonCyan }]}>
            {agent.trial_days || 7} days FREE
          </Text>
        </View>
        <View style={[styles.pricingDivider, { backgroundColor: colors.textSecondary + '20' }]} />
        <View style={styles.pricingRow}>
          <Text style={[styles.pricingLabelBold, { color: colors.textPrimary }]}>
            Due Today
          </Text>
          <Text style={[styles.pricingValueBold, { color: colors.neonCyan }]}>
            ₹0
          </Text>
        </View>
        <Text style={[styles.pricingNote, { color: colors.textSecondary }]}>
          Billing starts after trial ends
        </Text>
      </View>

      {/* Billing Information */}
      <View style={{ marginTop: spacing.lg }}>
        <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>
          Billing Information
        </Text>

        {/* Full Name */}
        <View style={{ marginTop: spacing.md }}>
          <Text style={[styles.fieldLabel, { color: colors.textPrimary }]}>
            Full Name *
          </Text>
          <TextInput
            style={[
              styles.textInput,
              {
                backgroundColor: colors.card,
                color: colors.textPrimary,
                borderColor: errors.fullName ? '#ef4444' : colors.textSecondary + '40',
                borderWidth: 1,
              },
            ]}
            placeholder="John Doe"
            placeholderTextColor={colors.textSecondary}
            value={paymentData.fullName}
            onChangeText={(text) => {
              onPaymentDataChange('fullName', text);
              if (errors.fullName) {
                setErrors({ ...errors, fullName: '' });
              }
            }}
          />
          {errors.fullName && (
            <Text style={[styles.errorText, { color: '#ef4444' }]}>
              {errors.fullName}
            </Text>
          )}
        </View>

        {/* Email */}
        <View style={{ marginTop: spacing.md }}>
          <Text style={[styles.fieldLabel, { color: colors.textPrimary }]}>
            Email Address *
          </Text>
          <TextInput
            style={[
              styles.textInput,
              {
                backgroundColor: colors.card,
                color: colors.textPrimary,
                borderColor: errors.email ? '#ef4444' : colors.textSecondary + '40',
                borderWidth: 1,
              },
            ]}
            placeholder="john@example.com"
            placeholderTextColor={colors.textSecondary}
            value={paymentData.email}
            onChangeText={(text) => {
              onPaymentDataChange('email', text);
              if (errors.email) {
                setErrors({ ...errors, email: '' });
              }
            }}
            keyboardType="email-address"
            autoCapitalize="none"
          />
          {errors.email && (
            <Text style={[styles.errorText, { color: '#ef4444' }]}>
              {errors.email}
            </Text>
          )}
        </View>

        {/* Phone */}
        <View style={{ marginTop: spacing.md }}>
          <Text style={[styles.fieldLabel, { color: colors.textPrimary }]}>
            Phone Number *
          </Text>
          <TextInput
            style={[
              styles.textInput,
              {
                backgroundColor: colors.card,
                color: colors.textPrimary,
                borderColor: errors.phone ? '#ef4444' : colors.textSecondary + '40',
                borderWidth: 1,
              },
            ]}
            placeholder="9876543210"
            placeholderTextColor={colors.textSecondary}
            value={paymentData.phone}
            onChangeText={(text) => {
              onPaymentDataChange('phone', text);
              if (errors.phone) {
                setErrors({ ...errors, phone: '' });
              }
            }}
            keyboardType="phone-pad"
          />
          {errors.phone && (
            <Text style={[styles.errorText, { color: '#ef4444' }]}>
              {errors.phone}
            </Text>
          )}
        </View>
      </View>

      {/* Payment Method Selection */}
      <View style={{ marginTop: spacing.lg }}>
        <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>
          Payment Method
        </Text>
        <Text style={[styles.fieldHint, { color: colors.textSecondary, marginTop: spacing.xs }]}>
          Select your preferred payment method (Razorpay integration in Story 2.9)
        </Text>

        <View style={{ marginTop: spacing.md }}>
          {/* Card / Credit */}
          <TouchableOpacity
            style={[
              styles.paymentMethodButton,
              {
                backgroundColor: colors.card,
                borderColor:
                  paymentData.paymentMethod === 'card'
                    ? colors.neonCyan
                    : colors.textSecondary + '40',
                borderWidth: 2,
              },
            ]}
            onPress={() => {
              onPaymentDataChange('paymentMethod', 'card');
              if (errors.paymentMethod) {
                setErrors({ ...errors, paymentMethod: '' });
              }
            }}
          >
            <Text style={{ fontSize: 24 }}>💳</Text>
            <Text style={[styles.paymentMethodText, { color: colors.textPrimary }]}>
              Credit / Debit Card
            </Text>
          </TouchableOpacity>

          {/* UPI */}
          <TouchableOpacity
            style={[
              styles.paymentMethodButton,
              {
                backgroundColor: colors.card,
                borderColor:
                  paymentData.paymentMethod === 'upi'
                    ? colors.neonCyan
                    : colors.textSecondary + '40',
                borderWidth: 2,
                marginTop: spacing.sm,
              },
            ]}
            onPress={() => {
              onPaymentDataChange('paymentMethod', 'upi');
              if (errors.paymentMethod) {
                setErrors({ ...errors, paymentMethod: '' });
              }
            }}
          >
            <Text style={{ fontSize: 24 }}>📱</Text>
            <Text style={[styles.paymentMethodText, { color: colors.textPrimary }]}>
              UPI
            </Text>
          </TouchableOpacity>

          {/* Net Banking */}
          <TouchableOpacity
            style={[
              styles.paymentMethodButton,
              {
                backgroundColor: colors.card,
                borderColor:
                  paymentData.paymentMethod === 'netbanking'
                    ? colors.neonCyan
                    : colors.textSecondary + '40',
                borderWidth: 2,
                marginTop: spacing.sm,
              },
            ]}
            onPress={() => {
              onPaymentDataChange('paymentMethod', 'netbanking');
              if (errors.paymentMethod) {
                setErrors({ ...errors, paymentMethod: '' });
              }
            }}
          >
            <Text style={{ fontSize: 24 }}>🏦</Text>
            <Text style={[styles.paymentMethodText, { color: colors.textPrimary }]}>
              Net Banking
            </Text>
          </TouchableOpacity>
        </View>

        {errors.paymentMethod && (
          <Text style={[styles.errorText, { color: '#ef4444', marginTop: spacing.sm }]}>
            {errors.paymentMethod}
          </Text>
        )}
      </View>

      {/* Terms & Conditions */}
      <View style={{ marginTop: spacing.lg }}>
        <TouchableOpacity
          style={styles.checkboxRow}
          onPress={() => {
            onPaymentDataChange('acceptedTerms', !paymentData.acceptedTerms);
            if (errors.acceptedTerms) {
              setErrors({ ...errors, acceptedTerms: '' });
            }
          }}
        >
          <View
            style={[
              styles.checkbox,
              {
                backgroundColor: paymentData.acceptedTerms ? colors.neonCyan : 'transparent',
                borderColor: errors.acceptedTerms
                  ? '#ef4444'
                  : paymentData.acceptedTerms
                  ? colors.neonCyan
                  : colors.textSecondary,
                borderWidth: 2,
              },
            ]}
          >
            {paymentData.acceptedTerms && (
              <Text style={{ color: colors.black, fontSize: 14, fontWeight: 'bold' }}>
                ✓
              </Text>
            )}
          </View>
          <Text style={[styles.checkboxLabel, { color: colors.textSecondary }]}>
            I accept the{' '}
            <Text style={{ color: colors.neonCyan }}>Terms & Conditions</Text> and{' '}
            <Text style={{ color: colors.neonCyan }}>Privacy Policy</Text>
          </Text>
        </TouchableOpacity>
        {errors.acceptedTerms && (
          <Text style={[styles.errorText, { color: '#ef4444' }]}>
            {errors.acceptedTerms}
          </Text>
        )}
      </View>

      {/* Payment Security Info */}
      <View
        style={[
          styles.securityBanner,
          { backgroundColor: `${colors.neonCyan}11`, marginTop: spacing.lg },
        ]}
      >
        <Text style={[styles.securityText, { color: colors.textSecondary }]}>
          🔒 Your payment information is secure and encrypted
        </Text>
        <Text
          style={[
            styles.securityText,
            { color: colors.textSecondary, marginTop: spacing.xs },
          ]}
        >
          You won't be charged until after your {agent.trial_days || 7}-day trial ends
        </Text>
      </View>

      {/* Action Buttons */}
      <View style={{ marginTop: spacing.xl }}>
        <TouchableOpacity
          style={[styles.primaryButton, { backgroundColor: colors.neonCyan }]}
          onPress={handleComplete}
        >
          <Text style={[styles.primaryButtonText, { color: colors.black }]}>
            Start Trial
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.secondaryButton, { marginTop: spacing.md }]}
          onPress={onBack}
        >
          <Text style={[styles.secondaryButtonText, { color: colors.textSecondary }]}>
            Back
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

// Main wizard component
export const HireWizardScreen = () => {
  const route = useRoute<HireWizardRouteProp>();
  const navigation = useNavigation();
  const { colors, spacing } = useTheme();
  const { agentId } = route.params;

  const [currentStep, setCurrentStep] = useState(1);
  
  // Trial data state
  const [trialData, setTrialData] = useState({
    startDate: '',
    goals: '',
    deliverables: '',
  });

  // Payment data state
  const [paymentData, setPaymentData] = useState({
    fullName: '',
    email: '',
    phone: '',
    paymentMethod: '',
    acceptedTerms: false,
  });

  // Handle trial data changes
  const handleTrialDataChange = (field: string, value: string) => {
    setTrialData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  // Handle payment data changes
  const handlePaymentDataChange = (field: string, value: any) => {
    setPaymentData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  // Fetch agent data
  const { data: agent, isLoading, error, refetch } = useAgentDetail(agentId);

  // Handle navigation
  const handleCancel = () => {
    navigation.goBack();
  };

  const handleComplete = () => {
    // TODO: Submit hire request to API (Story 2.10)
    console.log('Hire request submitted for agent:', agentId);
    console.log('Trial data:', trialData);
    console.log('Payment data:', paymentData);
    // Navigate to confirmation screen
    (navigation.navigate as any)('HireConfirmation', { 
      agentId, 
      trialData,
      paymentData 
    });
  };

  // Loading state
  if (isLoading) {
    return <LoadingSpinner message="Loading agent details..." />;
  }

  // Error state
  if (error || !agent) {
    return (
      <ErrorView
        message={error?.message || 'Agent not found'}
        onRetry={refetch}
      />
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.black }]}>
      {/* Progress Indicator */}
      <View style={[styles.progressContainer, { backgroundColor: colors.card }]}>
        {[1, 2, 3].map((step) => (
          <View key={step} style={styles.progressStep}>
            <View
              style={[
                styles.progressDot,
                {
                  backgroundColor:
                    currentStep >= step ? colors.neonCyan : colors.textSecondary,
                },
              ]}
            />
            {step < 3 && (
              <View
                style={[
                  styles.progressLine,
                  {
                    backgroundColor:
                      currentStep > step ? colors.neonCyan : colors.textSecondary,
                  },
                ]}
              />
            )}
          </View>
        ))}
      </View>

      {/* Step Labels */}
      <View style={styles.stepLabelsContainer}>
        <Text
          style={[
            styles.stepLabel,
            { color: currentStep === 1 ? colors.neonCyan : colors.textSecondary },
          ]}
        >
          Confirm
        </Text>
        <Text
          style={[
            styles.stepLabel,
            { color: currentStep === 2 ? colors.neonCyan : colors.textSecondary },
          ]}
        >
          Trial Details
        </Text>
        <Text
          style={[
            styles.stepLabel,
            { color: currentStep === 3 ? colors.neonCyan : colors.textSecondary },
          ]}
        >
          Payment
        </Text>
      </View>

      {/* Step Content */}
      <ScrollView style={styles.content}>
        {currentStep === 1 && (
          <Step1ConfirmAgent
            agent={agent}
            onNext={() => setCurrentStep(2)}
            onCancel={handleCancel}
          />
        )}
        {currentStep === 2 && (
          <Step2TrialDetails
            trialData={trialData}
            onTrialDataChange={handleTrialDataChange}
            onNext={() => setCurrentStep(3)}
            onBack={() => setCurrentStep(1)}
          />
        )}
        {currentStep === 3 && (
          <Step3Payment
            agent={agent}
            paymentData={paymentData}
            onPaymentDataChange={handlePaymentDataChange}
            onComplete={handleComplete}
            onBack={() => setCurrentStep(2)}
          />
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  progressContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 20,
    paddingHorizontal: 40,
  },
  progressStep: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  progressDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  progressLine: {
    width: 50,
    height: 2,
  },
  stepLabelsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  stepLabel: {
    fontSize: 12,
    fontWeight: '600',
  },
  content: {
    flex: 1,
  },
  stepTitle: {
    fontSize: 28,
    fontWeight: '700',
  },
  stepSubtitle: {
    fontSize: 16,
    lineHeight: 24,
  },
  agentCard: {
    marginTop: 20,
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  avatarText: {
    fontSize: 32,
    fontWeight: '700',
  },
  agentName: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 8,
  },
  agentSpecialty: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  badgeContainer: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  badge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  pricingSection: {
    alignItems: 'center',
    marginTop: 16,
  },
  priceLabel: {
    fontSize: 14,
    marginBottom: 4,
  },
  price: {
    fontSize: 32,
    fontWeight: '700',
    marginBottom: 4,
  },
  trialBanner: {
    marginTop: 20,
    padding: 16,
    borderRadius: 12,
    width: '100%',
  },
  trialText: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
    textAlign: 'center',
  },
  trialSubtext: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 8,
  },
  stepItem: {
    fontSize: 14,
    lineHeight: 20,
  },
  formCard: {
    padding: 20,
    borderRadius: 12,
  },
  securityBanner: {
    padding: 16,
    borderRadius: 12,
  },
  securityText: {
    fontSize: 14,
    lineHeight: 20,
    textAlign: 'center',
  },
  primaryButton: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  primaryButtonText: {
    fontSize: 16,
    fontWeight: '700',
  },
  secondaryButton: {
    paddingVertical: 16,
    alignItems: 'center',
  },
  secondaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  fieldLabel: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  textInput: {
    padding: 16,
    borderRadius: 8,
    fontSize: 16,
  },
  textArea: {
    padding: 16,
    borderRadius: 8,
    fontSize: 16,
    minHeight: 100,
  },
  errorText: {
    fontSize: 14,
    marginTop: 4,
  },
  fieldHint: {
    fontSize: 12,
    marginTop: 4,
    lineHeight: 16,
  },
  pricingSummary: {
    padding: 20,
    borderRadius: 12,
  },
  pricingTitle: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 16,
  },
  pricingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  pricingLabel: {
    fontSize: 14,
  },
  pricingValue: {
    fontSize: 16,
    fontWeight: '600',
  },
  pricingDivider: {
    height: 1,
    marginVertical: 12,
  },
  pricingLabelBold: {
    fontSize: 16,
    fontWeight: '700',
  },
  pricingValueBold: {
    fontSize: 20,
    fontWeight: '700',
  },
  pricingNote: {
    fontSize: 12,
    textAlign: 'center',
    marginTop: 8,
  },
  paymentMethodButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
  },
  paymentMethodText: {
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 12,
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 4,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  checkboxLabel: {
    flex: 1,
    fontSize: 14,
    lineHeight: 20,
  },
});
