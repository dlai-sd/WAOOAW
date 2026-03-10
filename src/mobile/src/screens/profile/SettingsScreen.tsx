/**
 * Settings Screen (MOBILE-FUNC-1 S4)
 *
 * App preferences: notifications toggle, privacy policy, terms, sign-out.
 */

import React from 'react';
import {
  View,
  Text,
  SafeAreaView,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { useTheme } from '@/hooks/useTheme';
import { useAuthStore } from '../../store/authStore';
import type { ProfileStackScreenProps } from '@/navigation/types';

type Props = ProfileStackScreenProps<'Settings'>;

export const SettingsScreen = ({ navigation }: Props) => {
  const { colors, spacing, typography } = useTheme();
  const logout = useAuthStore((state) => state.logout);

  const handleSignOut = async () => {
    try {
      await logout();
    } catch {
      // logout cleans up state regardless
    }
  };

  const rowStyle = {
    flexDirection: 'row' as const,
    alignItems: 'center' as const,
    justifyContent: 'space-between' as const,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.screenPadding.horizontal,
    borderBottomWidth: 1,
    borderBottomColor: colors.border + '40',
  };

  const labelStyle = {
    color: colors.textPrimary,
    fontFamily: typography.fontFamily.body,
    fontSize: 16,
  };

  const sectionHeaderStyle = {
    color: colors.textSecondary,
    fontFamily: typography.fontFamily.body,
    fontSize: 12,
    textTransform: 'uppercase' as const,
    letterSpacing: 1,
    paddingHorizontal: spacing.screenPadding.horizontal,
    paddingTop: spacing.lg,
    paddingBottom: spacing.sm,
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.black }}>
      <View
        style={{
          paddingHorizontal: spacing.screenPadding.horizontal,
          paddingTop: spacing.md,
          paddingBottom: spacing.sm,
        }}
      >
        <TouchableOpacity
          onPress={() => navigation.goBack()}
          style={{ marginBottom: spacing.md }}
        >
          <Text
            style={{
              color: colors.neonCyan,
              fontFamily: typography.fontFamily.body,
              fontSize: 14,
            }}
          >
            ← Back
          </Text>
        </TouchableOpacity>
        <Text
          style={{
            color: colors.textPrimary,
            fontFamily: typography.fontFamily.display,
            fontSize: 24,
            fontWeight: 'bold',
          }}
        >
          Settings
        </Text>
      </View>

      <ScrollView>
        {/* Preferences */}
        <Text style={sectionHeaderStyle}>Preferences</Text>
        <TouchableOpacity
          style={rowStyle}
          onPress={() => navigation.navigate('Notifications')}
        >
          <View style={{ flex: 1 }}>
            <Text style={labelStyle}>🔔  Manage Notifications</Text>
            <Text style={{ color: colors.textSecondary, fontFamily: typography.fontFamily.body, fontSize: 12, marginTop: 2 }}>
              Push permissions, alert types, and approval routing previews
            </Text>
          </View>
          <Text style={{ color: colors.textSecondary, fontSize: 18 }}>›</Text>
        </TouchableOpacity>

        {/* Legal */}
        <Text style={sectionHeaderStyle}>Legal</Text>
        <TouchableOpacity
          style={rowStyle}
          onPress={() => navigation.navigate('PrivacyPolicy')}
        >
          <Text style={labelStyle}>🔒  Privacy Policy</Text>
          <Text style={{ color: colors.textSecondary, fontSize: 18 }}>›</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={rowStyle}
          onPress={() => navigation.navigate('TermsOfService')}
        >
          <Text style={labelStyle}>📄  Terms of Service</Text>
          <Text style={{ color: colors.textSecondary, fontSize: 18 }}>›</Text>
        </TouchableOpacity>

        {/* Account */}
        <Text style={sectionHeaderStyle}>Account</Text>
        <TouchableOpacity
          style={{
            ...rowStyle,
            borderBottomWidth: 0,
            marginTop: spacing.sm,
          }}
          onPress={handleSignOut}
        >
          <Text
            style={{
              color: colors.error,
              fontFamily: typography.fontFamily.bodyBold,
              fontSize: 16,
            }}
          >
            Sign Out
          </Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
};
