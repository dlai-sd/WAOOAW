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

const Step3Payment = ({ onComplete, onBack }: any) => {
  const { colors, spacing } = useTheme();

  return (
    <View style={{ padding: spacing.lg }}>
      <Text style={[styles.stepTitle, { color: colors.textPrimary }]}>
        Payment Details
      </Text>
      <Text style={[styles.stepSubtitle, { color: colors.textSecondary, marginTop: spacing.sm }]}>
        Add a payment method (no charge during trial)
      </Text>

      {/* Placeholder for payment form */}
      <View style={[styles.formCard, { backgroundColor: colors.card, marginTop: spacing.lg }]}>
        <Text style={{ color: colors.textSecondary }}>
          Payment integration will be implemented in Story 2.8 & 2.9
        </Text>
        <Text style={{ color: colors.textSecondary, marginTop: spacing.sm }}>
          • Razorpay SDK integration
        </Text>
        <Text style={{ color: colors.textSecondary }}>
          • Card / UPI / NetBanking options
        </Text>
        <Text style={{ color: colors.textSecondary }}>
          • Secure payment processing
        </Text>
      </View>

      {/* Payment Security Info */}
      <View style={[styles.securityBanner, { backgroundColor: `${colors.neonCyan}11`, marginTop: spacing.lg }]}>
        <Text style={[styles.securityText, { color: colors.textSecondary }]}>
          🔒 Your payment information is secure and encrypted
        </Text>
        <Text style={[styles.securityText, { color: colors.textSecondary, marginTop: spacing.xs }]}>
          You won't be charged until after your 7-day trial ends
        </Text>
      </View>

      {/* Action Buttons */}
      <View style={{ marginTop: spacing.xl }}>
        <TouchableOpacity
          style={[styles.primaryButton, { backgroundColor: colors.neonCyan }]}
          onPress={onComplete}
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

  // Handle trial data changes
  const handleTrialDataChange = (field: string, value: string) => {
    setTrialData((prev) => ({
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
    console.log('Hire request submitted for agent:', agentId, 'with trial data:', trialData);
    // Navigate to confirmation screen
    (navigation.navigate as any)('HireConfirmation', { agentId, trialData });
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
});
