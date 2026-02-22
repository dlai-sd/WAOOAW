/**
 * Hire Confirmation Screen - Trial activation success
 * 
 * Shows successful trial activation with:
 * - Agent details
 * - Trial period info
 * - Next steps
 * - Quick actions
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  SafeAreaView,
  TouchableOpacity,
} from 'react-native';
import { useRoute, useNavigation, RouteProp } from '@react-navigation/native';
import { useTheme } from '@/hooks/useTheme';
import { useAgentDetail } from '@/hooks/useAgentDetail';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { ErrorView } from '@/components/ErrorView';

// Navigation types
type HireConfirmationParams = {
  agentId: string;
  trialData?: {
    startDate: string;
    goals: string;
    deliverables: string;
  };
  paymentData?: {
    fullName: string;
    email: string;
    phone: string;
    paymentMethod: string;
    acceptedTerms: boolean;
  };
};
type HireConfirmationRouteProp = RouteProp<
  { HireConfirmation: HireConfirmationParams },
  'HireConfirmation'
>;

export const HireConfirmationScreen = () => {
  const route = useRoute<HireConfirmationRouteProp>();
  const navigation = useNavigation();
  const { colors, spacing } = useTheme();
  const { agentId, trialData, paymentData } = route.params;

  // Fetch agent data
  const { data: agent, isLoading, error, refetch } = useAgentDetail(agentId);

  // Calculate trial end date (7 days from start)
  const calculateTrialEndDate = (startDate: string, trialDays: number = 7) => {
    if (!startDate) return '';
    const start = new Date(startDate);
    const end = new Date(start.getTime() + trialDays * 24 * 60 * 60 * 1000);
    return end.toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  // Handle navigation
  const handleGoToMyAgents = () => {
    (navigation.navigate as any)('MyAgents');
  };

  const handleGoToTrialDashboard = () => {
    (navigation.navigate as any)('TrialDashboard', { agentId });
  };

  const handleGoHome = () => {
    (navigation.navigate as any)('Discover');
  };

  // Loading state
  if (isLoading) {
    return <LoadingSpinner message="Loading confirmation..." />;
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

  const trialEndDate = trialData?.startDate
    ? calculateTrialEndDate(trialData.startDate, agent.trial_days || 7)
    : '';

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.black }]}>
      <ScrollView style={styles.content}>
        {/* Success Icon */}
        <View style={styles.successIconContainer}>
          <View style={[styles.successIcon, { backgroundColor: `${colors.neonCyan}22` }]}>
            <Text style={[styles.successEmoji, { color: colors.neonCyan }]}>
              🎉
            </Text>
          </View>
        </View>

        {/* Success Message */}
        <Text style={[styles.title, { color: colors.textPrimary }]}>
          Trial Activated!
        </Text>
        <Text style={[styles.subtitle, { color: colors.textSecondary }]}>
          Your {agent.trial_days || 7}-day free trial has started successfully
        </Text>

        {/* Agent Summary Card */}
        <View style={[styles.agentCard, { backgroundColor: colors.card, marginTop: spacing.xl }]}>
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

          {/* Trial Period Info */}
          <View style={[styles.trialInfoCard, { backgroundColor: `${colors.neonCyan}11`, marginTop: spacing.md }]}>
            <View style={styles.trialInfoRow}>
              <Text style={[styles.trialInfoLabel, { color: colors.textSecondary }]}>
                Trial Period
              </Text>
              <Text style={[styles.trialInfoValue, { color: colors.textPrimary }]}>
                {agent.trial_days || 7} days
              </Text>
            </View>
            {trialData?.startDate && (
              <>
                <View style={styles.trialInfoRow}>
                  <Text style={[styles.trialInfoLabel, { color: colors.textSecondary }]}>
                    Start Date
                  </Text>
                  <Text style={[styles.trialInfoValue, { color: colors.textPrimary }]}>
                    {new Date(trialData.startDate).toLocaleDateString('en-IN', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                    })}
                  </Text>
                </View>
                <View style={styles.trialInfoRow}>
                  <Text style={[styles.trialInfoLabel, { color: colors.textSecondary }]}>
                    End Date
                  </Text>
                  <Text style={[styles.trialInfoValue, { color: colors.neonCyan }]}>
                    {trialEndDate}
                  </Text>
                </View>
              </>
            )}
          </View>
        </View>

        {/* What Happens Next */}
        <View style={{ marginTop: spacing.xl }}>
          <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>
            What happens next?
          </Text>
          <View style={{ marginTop: spacing.md }}>
            {[
              {
                emoji: '🚀',
                title: 'Agent starts working',
                description: 'Your agent will begin working on your trial goals immediately',
              },
              {
                emoji: '📊',
                title: 'Track progress',
                description: 'Monitor deliverables and progress in your trial dashboard',
              },
              {
                emoji: '📬',
                title: 'Receive deliverables',
                description: 'Get regular updates and deliverables throughout the trial',
              },
              {
                emoji: '✅',
                title: 'Decide to hire',
                description: `Review results and decide before ${trialEndDate || 'trial ends'}`,
              },
            ].map((step, index) => (
              <View
                key={index}
                style={[
                  styles.nextStepCard,
                  { backgroundColor: colors.card, marginBottom: spacing.sm },
                ]}
              >
                <Text style={styles.nextStepEmoji}>{step.emoji}</Text>
                <View style={{ flex: 1, marginLeft: spacing.md }}>
                  <Text style={[styles.nextStepTitle, { color: colors.textPrimary }]}>
                    {step.title}
                  </Text>
                  <Text style={[styles.nextStepDescription, { color: colors.textSecondary }]}>
                    {step.description}
                  </Text>
                </View>
              </View>
            ))}
          </View>
        </View>

        {/* Trial Goals Reminder */}
        {trialData?.goals && (
          <View style={[styles.goalsCard, { backgroundColor: colors.card, marginTop: spacing.lg }]}>
            <Text style={[styles.goalsTitle, { color: colors.textPrimary }]}>
              Your Trial Goals
            </Text>
            <Text style={[styles.goalsText, { color: colors.textSecondary, marginTop: spacing.sm }]}>
              {trialData.goals}
            </Text>
          </View>
        )}

        {/* Important Notice */}
        <View style={[styles.noticeCard, { backgroundColor: `${colors.neonCyan}11`, marginTop: spacing.lg }]}>
          <Text style={[styles.noticeTitle, { color: colors.neonCyan }]}>
            💡 Important
          </Text>
          <Text style={[styles.noticeText, { color: colors.textSecondary, marginTop: spacing.xs }]}>
            You'll receive a reminder 2 days before your trial ends. You can cancel anytime during
            the trial at no charge.
          </Text>
        </View>

        {/* Action Buttons */}
        <View style={{ marginTop: spacing.xl, paddingBottom: spacing.xl }}>
          <TouchableOpacity
            style={[styles.primaryButton, { backgroundColor: colors.neonCyan }]}
            onPress={handleGoToTrialDashboard}
          >
            <Text style={[styles.primaryButtonText, { color: colors.black }]}>
              Go to Trial Dashboard
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.secondaryButton, { marginTop: spacing.md }]}
            onPress={handleGoToMyAgents}
          >
            <Text style={[styles.secondaryButtonText, { color: colors.textSecondary }]}>
              View My Agents
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.tertiaryButton, { marginTop: spacing.sm }]}
            onPress={handleGoHome}
          >
            <Text style={[styles.tertiaryButtonText, { color: colors.textSecondary }]}>
              Back to Discover
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 24,
  },
  successIconContainer: {
    alignItems: 'center',
    marginTop: 32,
  },
  successIcon: {
    width: 100,
    height: 100,
    borderRadius: 50,
    alignItems: 'center',
    justifyContent: 'center',
  },
  successEmoji: {
    fontSize: 48,
  },
  title: {
    fontSize: 32,
    fontWeight: '700',
    textAlign: 'center',
    marginTop: 24,
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
    marginTop: 8,
    lineHeight: 24,
  },
  agentCard: {
    padding: 24,
    borderRadius: 16,
    alignItems: 'center',
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: 32,
    fontWeight: '700',
  },
  agentName: {
    fontSize: 24,
    fontWeight: '700',
    marginTop: 16,
    textAlign: 'center',
  },
  agentSpecialty: {
    fontSize: 16,
    marginTop: 8,
    textAlign: 'center',
  },
  trialInfoCard: {
    width: '100%',
    padding: 16,
    borderRadius: 12,
  },
  trialInfoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  trialInfoLabel: {
    fontSize: 14,
  },
  trialInfoValue: {
    fontSize: 16,
    fontWeight: '600',
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
  },
  nextStepCard: {
    flexDirection: 'row',
    padding: 16,
    borderRadius: 12,
    alignItems: 'flex-start',
  },
  nextStepEmoji: {
    fontSize: 24,
  },
  nextStepTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  nextStepDescription: {
    fontSize: 14,
    marginTop: 4,
    lineHeight: 20,
  },
  goalsCard: {
    padding: 20,
    borderRadius: 12,
  },
  goalsTitle: {
    fontSize: 18,
    fontWeight: '700',
  },
  goalsText: {
    fontSize: 14,
    lineHeight: 22,
  },
  noticeCard: {
    padding: 16,
    borderRadius: 12,
  },
  noticeTitle: {
    fontSize: 16,
    fontWeight: '700',
  },
  noticeText: {
    fontSize: 14,
    lineHeight: 20,
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
  tertiaryButton: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  tertiaryButtonText: {
    fontSize: 14,
    fontWeight: '500',
  },
});
