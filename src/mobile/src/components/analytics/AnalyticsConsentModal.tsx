/**
 * Analytics Consent Modal
 * GDPR-compliant consent for Firebase Analytics & Crashlytics
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  Modal,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { theme } from '../../theme';

const CONSENT_KEY = 'analytics_consent';
const CONSENT_VERSION = '1.0'; // Increment when policy changes materially

interface AnalyticsConsentModalProps {
  onConsentChange?: (granted: boolean) => void;
}

export const AnalyticsConsentModal: React.FC<AnalyticsConsentModalProps> = ({
  onConsentChange,
}) => {
  const [visible, setVisible] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkConsent();
  }, []);

  const checkConsent = async () => {
    try {
      const consent = await AsyncStorage.getItem(CONSENT_KEY);
      const consentVersion = await AsyncStorage.getItem(`${CONSENT_KEY}_version`);

      // Show modal if:
      // 1. No consent recorded yet
      // 2. Consent version is outdated
      if (!consent || consentVersion !== CONSENT_VERSION) {
        setVisible(true);
      }
    } catch (error) {
      console.error('[AnalyticsConsent] Failed to check consent:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = async () => {
    try {
      await AsyncStorage.setItem(CONSENT_KEY, 'true');
      await AsyncStorage.setItem(`${CONSENT_KEY}_version`, CONSENT_VERSION);
      await AsyncStorage.setItem(`${CONSENT_KEY}_timestamp`, new Date().toISOString());
      
      setVisible(false);
      onConsentChange?.(true);
    } catch (error) {
      console.error('[AnalyticsConsent] Failed to save consent:', error);
    }
  };

  const handleDecline = async () => {
    try {
      await AsyncStorage.setItem(CONSENT_KEY, 'false');
      await AsyncStorage.setItem(`${CONSENT_KEY}_version`, CONSENT_VERSION);
      await AsyncStorage.setItem(`${CONSENT_KEY}_timestamp`, new Date().toISOString());
      
      setVisible(false);
      onConsentChange?.(false);
    } catch (error) {
      console.error('[AnalyticsConsent] Failed to save consent:', error);
    }
  };

  if (loading || !visible) {
    return null;
  }

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      statusBarTranslucent
    >
      <View style={styles.overlay}>
        <View style={styles.modal}>
          <ScrollView contentContainerStyle={styles.scrollContent}>
            <Text style={styles.title}>Help Us Improve WAOOAW</Text>
            
            <Text style={styles.description}>
              We use analytics to understand how you use WAOOAW and make it better for everyone.
            </Text>

            <Text style={styles.sectionTitle}>What We Collect:</Text>
            <Text style={styles.bulletPoint}>• Screens you visit</Text>
            <Text style={styles.bulletPoint}>• Features you use</Text>
            <Text style={styles.bulletPoint}>• App performance data</Text>
            <Text style={styles.bulletPoint}>• Crash reports (to fix bugs)</Text>

            <Text style={styles.sectionTitle}>What We DON'T Collect:</Text>
            <Text style={styles.bulletPoint}>• Personal conversations with agents</Text>
            <Text style={styles.bulletPoint}>• Payment details</Text>
            <Text style={styles.bulletPoint}>• Sensitive personal information</Text>

            <Text style={styles.note}>
              All data is anonymized. You can change your preference anytime in Settings → Privacy.
            </Text>

            <Text style={styles.privacyLink}>
              Read our full Privacy Policy for details.
            </Text>
          </ScrollView>

          <View style={styles.buttons}>
            <TouchableOpacity
              style={styles.acceptButton}
              onPress={handleAccept}
              activeOpacity={0.8}
            >
              <Text style={styles.acceptButtonText}>Accept</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.declineButton}
              onPress={handleDecline}
              activeOpacity={0.8}
            >
              <Text style={styles.declineButtonText}>Decline</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.85)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: theme.spacing.lg,
  },
  modal: {
    backgroundColor: theme.colors.background.secondary,
    borderRadius: theme.borderRadius.xl,
    maxWidth: 480,
    width: '100%',
    maxHeight: '80%',
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: theme.colors.border.dark,
  },
  scrollContent: {
    padding: theme.spacing.xl,
  },
  title: {
    fontSize: 24,
    fontFamily: theme.typography.fontFamily.heading,
    color: theme.colors.text.primary,
    marginBottom: theme.spacing.md,
  },
  description: {
    fontSize: 16,
    fontFamily: theme.typography.fontFamily.body,
    color: theme.colors.text.secondary,
    lineHeight: 24,
    marginBottom: theme.spacing.lg,
  },
  sectionTitle: {
    fontSize: 18,
    fontFamily: theme.typography.fontFamily.heading,
    color: theme.colors.text.primary,
    marginTop: theme.spacing.md,
    marginBottom: theme.spacing.sm,
  },
  bulletPoint: {
    fontSize: 14,
    fontFamily: theme.typography.fontFamily.body,
    color: theme.colors.text.secondary,
    lineHeight: 20,
    marginBottom: theme.spacing.xs,
    paddingLeft: theme.spacing.md,
  },
  note: {
    fontSize: 13,
    fontFamily: theme.typography.fontFamily.body,
    color: theme.colors.text.tertiary,
    fontStyle: 'italic',
    lineHeight: 18,
    marginTop: theme.spacing.lg,
  },
  privacyLink: {
    fontSize: 13,
    fontFamily: theme.typography.fontFamily.body,
    color: theme.colors.primary,
    marginTop: theme.spacing.sm,
    textDecorationLine: 'underline',
  },
  buttons: {
    flexDirection: 'column',
    padding: theme.spacing.lg,
    gap: theme.spacing.md,
    borderTopWidth: 1,
    borderTopColor: theme.colors.border.dark,
  },
  acceptButton: {
    backgroundColor: theme.colors.primary,
    paddingVertical: theme.spacing.md,
    paddingHorizontal: theme.spacing.lg,
    borderRadius: theme.borderRadius.lg,
    alignItems: 'center',
  },
  acceptButtonText: {
    fontSize: 16,
    fontFamily: theme.typography.fontFamily.heading,
    color: theme.colors.text.primary,
    fontWeight: '600',
  },
  declineButton: {
    backgroundColor: 'transparent',
    paddingVertical: theme.spacing.md,
    paddingHorizontal: theme.spacing.lg,
    borderRadius: theme.borderRadius.lg,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: theme.colors.border.dark,
  },
  declineButtonText: {
    fontSize: 16,
    fontFamily: theme.typography.fontFamily.body,
    color: theme.colors.text.secondary,
  },
});
