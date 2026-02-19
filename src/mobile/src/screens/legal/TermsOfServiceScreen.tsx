/**
 * Terms of Service Screen
 * Displays WAOOAW terms of service with scroll view
 */

import React from 'react';
import {
  View,
  ScrollView,
  Text,
  StyleSheet,
  TouchableOpacity,
  Linking,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { theme } from '../../theme';

export const TermsOfServiceScreen: React.FC = () => {
  const navigation = useNavigation();

  const openWebTerms = async () => {
    const url = 'https://waooaw.com/terms-of-service';
    const canOpen = await Linking.canOpenURL(url);
    if (canOpen) {
      await Linking.openURL(url);
    }
  };

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.content}>
        <Text style={styles.title}>Terms of Service</Text>
        <Text style={styles.subtitle}>Last Updated: February 18, 2026</Text>

        <Text style={styles.sectionTitle}>1. Acceptance of Terms</Text>
        <Text style={styles.paragraph}>
          By accessing or using WAOOAW mobile application, you agree to be bound by these Terms of Service. If you do not agree, discontinue use immediately.
        </Text>

        <Text style={styles.sectionTitle}>2. Service Description</Text>
        <Text style={styles.paragraph}>
          WAOOAW is an AI agent marketplace where you can:
        </Text>
        <Text style={styles.bulletPoint}>• Browse and hire specialized AI agents</Text>
        <Text style={styles.bulletPoint}>• Start 7-day free trials</Text>
        <Text style={styles.bulletPoint}>• Receive deliverables from agents</Text>
        <Text style={styles.bulletPoint}>• Manage subscriptions</Text>

        <Text style={styles.sectionTitle}>3. User Accounts</Text>
        <Text style={styles.paragraph}>
          You must:
        </Text>
        <Text style={styles.bulletPoint}>• Provide accurate information during registration</Text>
        <Text style={styles.bulletPoint}>• Keep your account credentials secure</Text>
        <Text style={styles.bulletPoint}>• Be 18 years or older (or have parental consent)</Text>
        <Text style={styles.bulletPoint}>• Not share your account with others</Text>
        <Text style={styles.paragraph}>
          We reserve the right to suspend or terminate accounts that violate these terms.
        </Text>

        <Text style={styles.sectionTitle}>4. Trial Period & Subscriptions</Text>
        <Text style={styles.paragraph}>
          <Text style={styles.bold}>7-Day Free Trial:</Text>
        </Text>
        <Text style={styles.bulletPoint}>• You keep all deliverables even if you cancel</Text>
        <Text style={styles.bulletPoint}>• No charges during trial period</Text>
        <Text style={styles.bulletPoint}>• Cancel anytime before trial ends</Text>
        <Text style={styles.bulletPoint}>• Auto-converts to paid subscription after 7 days</Text>

        <Text style={styles.paragraph}>
          <Text style={styles.bold}>Paid Subscriptions:</Text>
        </Text>
        <Text style={styles.bulletPoint}>• Billed monthly in Indian Rupees (INR)</Text>
        <Text style={styles.bulletPoint}>• Pricing: ₹8,000 - ₹18,000/month per agent</Text>
        <Text style={styles.bulletPoint}>• Auto-renewal unless cancelled</Text>
        <Text style={styles.bulletPoint}>• No refunds for partial months</Text>
        <Text style={styles.bulletPoint}>• Cancel anytime via app settings</Text>

        <Text style={styles.sectionTitle}>5. Payment Terms</Text>
        <Text style={styles.paragraph}>
          Payments are processed by Razorpay. You agree to:
        </Text>
        <Text style={styles.bulletPoint}>• Provide valid payment information</Text>
        <Text style={styles.bulletPoint}>• Pay all charges on time</Text>
        <Text style={styles.bulletPoint}>• Authorize us to charge your payment method</Text>
        <Text style={styles.bulletPoint}>• Not dispute valid charges</Text>
        <Text style={styles.paragraph}>
          Failed payments may result in service suspension.
        </Text>

        <Text style={styles.sectionTitle}>6. Intellectual Property</Text>
        <Text style={styles.paragraph}>
          <Text style={styles.bold}>Agent Deliverables:</Text> You own all deliverables created by agents for you. This includes:
        </Text>
        <Text style={styles.bulletPoint}>• Marketing content (blog posts, ads, etc.)</Text>
        <Text style={styles.bulletPoint}>• Reports and analysis</Text>
        <Text style={styles.bulletPoint}>• Educational materials</Text>

        <Text style={styles.paragraph}>
          <Text style={styles.bold}>Platform IP:</Text> WAOOAW retains all rights to:
        </Text>
        <Text style={styles.bulletPoint}>• The app, website, and technology</Text>
        <Text style={styles.bulletPoint}>• Agent algorithms and models</Text>
        <Text style={styles.bulletPoint}>• WAOOAW branding and trademarks</Text>

        <Text style={styles.sectionTitle}>7. Prohibited Uses</Text>
        <Text style={styles.paragraph}>
          You may NOT:
        </Text>
        <Text style={styles.bulletPoint}>• Use agents for illegal activities</Text>
        <Text style={styles.bulletPoint}>• Reverse-engineer the platform</Text>
        <Text style={styles.bulletPoint}>• Share or resell agent access</Text>
        <Text style={styles.bulletPoint}>• Harass or abuse customer support</Text>
        <Text style={styles.bulletPoint}>• Attempt to hack or compromise security</Text>
        <Text style={styles.bulletPoint}>• Generate spam or harmful content via agents</Text>

        <Text style={styles.sectionTitle}>8. Limitation of Liability</Text>
        <Text style={styles.paragraph}>
          WAOOAW is provided "AS IS" without warranties. We are not liable for:
        </Text>
        <Text style={styles.bulletPoint}>• Agent errors or inaccuracies</Text>
        <Text style={styles.bulletPoint}>• Business losses from agent output</Text>
        <Text style={styles.bulletPoint}>• Service interruptions or downtime</Text>
        <Text style={styles.bulletPoint}>• Data loss (backup your deliverables)</Text>
        <Text style={styles.bulletPoint}>• Third-party payment processor issues</Text>

        <Text style={styles.paragraph}>
          Our total liability is limited to the amount you paid in the last 3 months.
        </Text>

        <Text style={styles.sectionTitle}>9. Termination</Text>
        <Text style={styles.paragraph}>
          Either party may terminate:
        </Text>
        <Text style={styles.bulletPoint}>• You can cancel subscriptions anytime in Settings</Text>
        <Text style={styles.bulletPoint}>• We can suspend accounts for terms violations</Text>
        <Text style={styles.bulletPoint}>• We can discontinue agents or services</Text>
        <Text style={styles.paragraph}>
          Upon termination, you retain access until subscription period ends.
        </Text>

        <Text style={styles.sectionTitle}>10. Dispute Resolution</Text>
        <Text style={styles.paragraph}>
          Disputes will be resolved through:
        </Text>
        <Text style={styles.bulletPoint}>• Good faith negotiation (first step)</Text>
        <Text style={styles.bulletPoint}>• Arbitration in Mumbai, India</Text>
        <Text style={styles.bulletPoint}>• Indian law governs these terms</Text>

        <Text style={styles.sectionTitle}>11. Changes to Terms</Text>
        <Text style={styles.paragraph}>
          We may update these terms. Major changes will be notified 30 days in advance via email or in-app notification. Continued use constitutes acceptance.
        </Text>

        <Text style={styles.sectionTitle}>12. Contact</Text>
        <Text style={styles.paragraph}>
          For questions about these terms:
        </Text>
        <Text style={styles.bulletPoint}>• Email: legal@waooaw.com</Text>
        <Text style={styles.bulletPoint}>• Support: support@waooaw.com</Text>
        <Text style={styles.bulletPoint}>• Address: WAOOAW Technologies Pvt Ltd, India</Text>

        <TouchableOpacity style={styles.button} onPress={openWebTerms}>
          <Text style={styles.buttonText}>View Full Terms on Web</Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background.primary,
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: theme.spacing.lg,
    paddingBottom: 40,
  },
  title: {
    fontSize: 28,
    fontFamily: theme.typography.fontFamily.heading,
    color: theme.colors.text.primary,
    marginBottom: theme.spacing.sm,
  },
  subtitle: {
    fontSize: 14,
    fontFamily: theme.typography.fontFamily.body,
    color: theme.colors.text.secondary,
    marginBottom: theme.spacing.xl,
  },
  sectionTitle: {
    fontSize: 20,
    fontFamily: theme.typography.fontFamily.heading,
    color: theme.colors.text.primary,
    marginTop: theme.spacing.xl,
    marginBottom: theme.spacing.md,
  },
  paragraph: {
    fontSize: 16,
    fontFamily: theme.typography.fontFamily.body,
    color: theme.colors.text.secondary,
    lineHeight: 24,
    marginBottom: theme.spacing.md,
  },
  bulletPoint: {
    fontSize: 16,
    fontFamily: theme.typography.fontFamily.body,
    color: theme.colors.text.secondary,
    lineHeight: 24,
    marginBottom: theme.spacing.sm,
    paddingLeft: theme.spacing.md,
  },
  bold: {
    fontFamily: theme.typography.fontFamily.heading,
    fontWeight: '600',
  },
  button: {
    backgroundColor: theme.colors.primary,
    padding: theme.spacing.md,
    borderRadius: theme.borderRadius.lg,
    alignItems: 'center',
    marginTop: theme.spacing.xl,
  },
  buttonText: {
    fontSize: 16,
    fontFamily: theme.typography.fontFamily.heading,
    color: theme.colors.text.primary,
  },
});
