/**
 * App Rating Prompt
 * Asks users to rate the app after positive experiences
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  Modal,
  StyleSheet,
  TouchableOpacity,
  Platform,
  Linking,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { theme } from '../../theme';

const RATING_PROMPT_KEY = 'app_rating_prompt';
const RATING_PROMPT_COUNT_KEY = 'app_rating_prompt_count';
const RATING_COMPLETED_KEY = 'app_rating_completed';

interface AppRatingPromptProps {
  trigger?: 'manual' | 'automatic';
  onDismiss?: () => void;
}

export const AppRatingPrompt: React.FC<AppRatingPromptProps> = ({
  trigger = 'automatic',
  onDismiss,
}) => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (trigger === 'automatic') {
      checkShouldShowPrompt();
    }
  }, [trigger]);

  const checkShouldShowPrompt = async () => {
    try {
      // Don't show if user already rated
      const completed = await AsyncStorage.getItem(RATING_COMPLETED_KEY);
      if (completed === 'true') {
        return;
      }

      // Check last prompt time (don't ask more than once per week)
      const lastPrompt = await AsyncStorage.getItem(RATING_PROMPT_KEY);
      if (lastPrompt) {
        const daysSinceLastPrompt = 
          (Date.now() - parseInt(lastPrompt)) / (1000 * 60 * 60 * 24);
        if (daysSinceLastPrompt < 7) {
          return;
        }
      }

      // Check prompt count (max 3 times total)
      const countStr = await AsyncStorage.getItem(RATING_PROMPT_COUNT_KEY);
      const count = countStr ? parseInt(countStr) : 0;
      if (count >= 3) {
        return;
      }

      // Show prompt
      setVisible(true);
      
      // Update prompt tracking
      await AsyncStorage.setItem(RATING_PROMPT_KEY, Date.now().toString());
      await AsyncStorage.setItem(RATING_PROMPT_COUNT_KEY, (count + 1).toString());
    } catch (error) {
      console.error('[AppRatingPrompt] Failed to check prompt:', error);
    }
  };

  const handleRate = async () => {
    try {
      // Mark as completed
      await AsyncStorage.setItem(RATING_COMPLETED_KEY, 'true');
      
      // Open app store
      const storeUrl = Platform.select({
        ios: 'https://apps.apple.com/app/idREPLACE_WITH_APP_STORE_ID?action=write-review',
        android: 'market://details?id=com.waooaw.app',
      });

      if (storeUrl) {
        const canOpen = await Linking.canOpenURL(storeUrl);
        if (canOpen) {
          await Linking.openURL(storeUrl);
        }
      }

      setVisible(false);
      onDismiss?.();
    } catch (error) {
      console.error('[AppRatingPrompt] Failed to open store:', error);
    }
  };

  const handleLater = async () => {
    setVisible(false);
    onDismiss?.();
  };

  const handleNever = async () => {
    try {
      // Mark as completed (won't show again)
      await AsyncStorage.setItem(RATING_COMPLETED_KEY, 'true');
      setVisible(false);
      onDismiss?.();
    } catch (error) {
      console.error('[AppRatingPrompt] Failed to save preference:', error);
    }
  };

  if (!visible) {
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
          <Text style={styles.emoji}>🌟</Text>
          <Text style={styles.title}>Enjoying WAOOAW?</Text>
          
          <Text style={styles.description}>
            If you love our AI agents, please take a moment to rate us. Your feedback helps us improve!
          </Text>

          <View style={styles.buttons}>
            <TouchableOpacity
              style={styles.rateButton}
              onPress={handleRate}
              activeOpacity={0.8}
            >
              <Text style={styles.rateButtonText}>⭐ Rate on {Platform.OS === 'ios' ? 'App Store' : 'Play Store'}</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.laterButton}
              onPress={handleLater}
              activeOpacity={0.8}
            >
              <Text style={styles.laterButtonText}>Maybe Later</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.neverButton}
              onPress={handleNever}
              activeOpacity={0.8}
            >
              <Text style={styles.neverButtonText}>Don't Ask Again</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

/**
 * Trigger rating prompt after positive events
 * Call this function when user completes key actions
 */
export const triggerRatingPromptIfAppropriate = async () => {
  try {
    // Check if already rated
    const completed = await AsyncStorage.getItem(RATING_COMPLETED_KEY);
    if (completed === 'true') {
      return false;
    }

    // Get positive action count
    const countStr = await AsyncStorage.getItem('positive_actions_count');
    const count = countStr ? parseInt(countStr) : 0;

    // Trigger after:
    // - 1st successful agent hire
    // - 3rd deliverable view
    // - 7th app open
    if (count === 1 || count === 3 || count === 7) {
      return true;
    }

    return false;
  } catch (error) {
    console.error('[AppRatingPrompt] Failed to check trigger:', error);
    return false;
  }
};

/**
 * Increment positive action counter
 * Call this after user completes positive actions
 */
export const incrementPositiveActions = async () => {
  try {
    const countStr = await AsyncStorage.getItem('positive_actions_count');
    const count = countStr ? parseInt(countStr) : 0;
    await AsyncStorage.setItem('positive_actions_count', (count + 1).toString());
  } catch (error) {
    console.error('[AppRatingPrompt] Failed to increment counter:', error);
  }
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
    backgroundColor: theme.colors.backgroundSecondary,
    borderRadius: theme.radius.xl,
    maxWidth: 400,
    width: '100%',
    padding: theme.spacing.xl,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  emoji: {
    fontSize: 64,
    marginBottom: theme.spacing.md,
  },
  title: {
    fontSize: 24,
    fontFamily: theme.typography.fontFamily.heading,
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.md,
    textAlign: 'center',
  },
  description: {
    fontSize: 16,
    fontFamily: theme.typography.fontFamily.body,
    color: theme.colors.textSecondary,
    lineHeight: 24,
    textAlign: 'center',
    marginBottom: theme.spacing.xl,
  },
  buttons: {
    width: '100%',
    gap: theme.spacing.md,
  },
  rateButton: {
    backgroundColor: theme.colors.neonCyan,
    paddingVertical: theme.spacing.md,
    paddingHorizontal: theme.spacing.lg,
    borderRadius: theme.radius.lg,
    alignItems: 'center',
  },
  rateButtonText: {
    fontSize: 16,
    fontFamily: theme.typography.fontFamily.heading,
    color: theme.colors.black,
    fontWeight: '600',
  },
  laterButton: {
    backgroundColor: 'transparent',
    paddingVertical: theme.spacing.md,
    paddingHorizontal: theme.spacing.lg,
    borderRadius: theme.radius.lg,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  laterButtonText: {
    fontSize: 16,
    fontFamily: theme.typography.fontFamily.body,
    color: theme.colors.textSecondary,
  },
  neverButton: {
    paddingVertical: theme.spacing.sm,
    alignItems: 'center',
  },
  neverButtonText: {
    fontSize: 14,
    fontFamily: theme.typography.fontFamily.body,
    color: theme.colors.textMuted,
  },
});
