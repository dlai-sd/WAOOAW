/**
 * Privacy Policy Screen
 * Displays WAOOAW privacy policy with scroll view
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

export const PrivacyPolicyScreen: React.FC = () => {
  const navigation = useNavigation();

  const openWebPolicy = async () => {
    const url = 'https://waooaw.com/privacy-policy';
    const canOpen = await Linking.canOpenURL(url);
    if (canOpen) {
      await Linking.openURL(url);
    }
  };

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.content}>
        <Text style={styles.title}>Privacy Policy</Text>
        <Text style={styles.subtitle}>Last Updated: February 18, 2026</Text>

        <Text style={styles.sectionTitle}>1. Information We Collect</Text>
        <Text style={styles.paragraph}>
          WAOOAW ("we," "our," or "us") collects the following information when you use our mobile application:
        </Text>
        <Text style={styles.bulletPoint}>• Email address and phone number (for authentication)</Text>
        <Text style={styles.bulletPoint}>• Profile information (name, preferences)</Text>
        <Text style={styles.bulletPoint}>• Usage data (screens visited, features used)</Text>
        <Text style={styles.bulletPoint}>• Device information (OS version, device model)</Text>
        <Text style={styles.bulletPoint}>• Payment information (processed by Razorpay, not stored by us)</Text>

        <Text style={styles.sectionTitle}>2. How We Use Your Information</Text>
        <Text style={styles.paragraph}>We use your information to:</Text>
        <Text style={styles.bulletPoint}>• Provide and improve our services</Text>
        <Text style={styles.bulletPoint}>• Process payments and manage subscriptions</Text>
        <Text style={styles.bulletPoint}>• Send notifications about agent activity</Text>
        <Text style={styles.bulletPoint}>• Analyze app performance and usage patterns</Text>
        <Text style={styles.bulletPoint}>• Prevent fraud and ensure security</Text>

        <Text style={styles.sectionTitle}>3. Data Sharing</Text>
        <Text style={styles.paragraph}>
          We share your data only with trusted third-party services:
        </Text>
        <Text style={styles.bulletPoint}>• Google (OAuth authentication)</Text>
        <Text style={styles.bulletPoint}>• Razorpay (payment processing)</Text>
        <Text style={styles.bulletPoint}>• Firebase (analytics, crash reporting)</Text>
        <Text style={styles.bulletPoint}>• Sentry (error tracking)</Text>
        <Text style={styles.paragraph}>
          We do NOT sell your personal data to third parties.
        </Text>

        <Text style={styles.sectionTitle}>4. Data Security</Text>
        <Text style={styles.paragraph}>
          We implement industry-standard security measures:
        </Text>
        <Text style={styles.bulletPoint}>• Encrypted data transmission (HTTPS/TLS)</Text>
        <Text style={styles.bulletPoint}>• Secure token storage on device (Expo SecureStore)</Text>
        <Text style={styles.bulletPoint}>• Regular security audits</Text>
        <Text style={styles.bulletPoint}>• Access controls and authentication</Text>

        <Text style={styles.sectionTitle}>5. Your Rights (GDPR)</Text>
        <Text style={styles.paragraph}>
          If you're in the EU, you have the right to:
        </Text>
        <Text style={styles.bulletPoint}>• Access your personal data</Text>
        <Text style={styles.bulletPoint}>• Request data deletion</Text>
        <Text style={styles.bulletPoint}>• Export your data</Text>
        <Text style={styles.bulletPoint}>• Opt-out of analytics</Text>
        <Text style={styles.bulletPoint}>• Withdraw consent at any time</Text>

        <Text style={styles.sectionTitle}>6. Data Retention</Text>
        <Text style={styles.paragraph}>
          We retain your data for as long as your account is active. After account deletion, we retain minimal data for legal compliance (transaction records) for 7 years as required by Indian tax law.
        </Text>

        <Text style={styles.sectionTitle}>7. Children's Privacy</Text>
        <Text style={styles.paragraph}>
          WAOOAW is not intended for users under 13. We do not knowingly collect data from children. If you believe a child has provided us with data, contact us immediately.
        </Text>

        <Text style={styles.sectionTitle}>8. Analytics & Cookies</Text>
        <Text style={styles.paragraph}>
          We use Firebase Analytics to understand app usage. You can opt-out in Settings. We do not use cookies in the mobile app.
        </Text>

        <Text style={styles.sectionTitle}>9. Changes to Policy</Text>
        <Text style={styles.paragraph}>
          We may update this policy. We'll notify you via email or in-app notification. Continued use after changes constitutes acceptance.
        </Text>

        <Text style={styles.sectionTitle}>10. Contact Us</Text>
        <Text style={styles.paragraph}>
          For privacy concerns, contact us at:
        </Text>
        <Text style={styles.bulletPoint}>• Email: privacy@waooaw.com</Text>
        <Text style={styles.bulletPoint}>• Address: WAOOAW Technologies Pvt Ltd, India</Text>

        <TouchableOpacity style={styles.button} onPress={openWebPolicy}>
          <Text style={styles.buttonText}>View Full Policy on Web</Text>
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
