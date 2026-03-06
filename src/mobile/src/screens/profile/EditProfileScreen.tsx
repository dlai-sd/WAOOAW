/**
 * Edit Profile Screen — E5-S1 (CP-NAV-1 Iteration 2)
 *
 * Allows the user to update full_name, phone, business_name and industry.
 * Calls PATCH /cp/profile on save.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  ScrollView,
  SafeAreaView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useTheme } from '../../hooks/useTheme';
import { useAuthStore, useCurrentUser } from '../../store/authStore';
import type { ProfileStackScreenProps } from '../../navigation/types';
import apiClient from '../../lib/apiClient';

type Props = ProfileStackScreenProps<'EditProfile'>;

interface ProfileForm {
  full_name: string;
  phone: string;
  business_name: string;
  industry: string;
}

export const EditProfileScreen = ({ navigation }: Props) => {
  const { colors, spacing, typography } = useTheme();
  const user = useCurrentUser();
  const updateUser = useAuthStore((state) => state.updateUser);

  const [form, setForm] = useState<ProfileForm>({
    full_name: user?.full_name ?? '',
    phone: user?.phone ?? '',
    business_name: user?.business_name ?? '',
    industry: '',
  });
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');

  const handleChange = (field: keyof ProfileForm, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    setStatus('loading');
    try {
      // Build the PATCH payload — only include non-empty fields
      const payload: Partial<ProfileForm> = {};
      if (form.full_name.trim()) payload.full_name = form.full_name.trim();
      if (form.phone.trim()) payload.phone = form.phone.trim();
      if (form.business_name.trim()) payload.business_name = form.business_name.trim();
      if (form.industry.trim()) payload.industry = form.industry.trim();

      if (Object.keys(payload).length > 0) {
        // Persist to CP backend first — source of truth
        await apiClient.patch('/api/v1/customers/profile', payload);
      }

      // Update local Zustand store to reflect changes immediately
      const storeUpdates: Partial<typeof user> = {};
      if (payload.full_name) storeUpdates.full_name = payload.full_name;
      if (payload.phone) storeUpdates.phone = payload.phone;
      if (payload.business_name) storeUpdates.business_name = payload.business_name;
      updateUser(storeUpdates);

      setStatus('success');
      Alert.alert('Profile updated', 'Your changes have been saved.', [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } catch (err: unknown) {
      setStatus('error');
      const message =
        err instanceof Error ? err.message : 'Failed to save profile. Please try again.';
      Alert.alert('Error', message);
    }
  };

  const fields: Array<{ label: string; field: keyof ProfileForm; placeholder: string; keyboardType?: 'default' | 'phone-pad' }> = [
    { label: 'Full Name', field: 'full_name', placeholder: 'Your full name' },
    { label: 'Phone', field: 'phone', placeholder: '+91 98765 43210', keyboardType: 'phone-pad' },
    { label: 'Business Name', field: 'business_name', placeholder: 'Your company' },
    { label: 'Industry', field: 'industry', placeholder: 'e.g. marketing, education' },
  ];

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.black }]}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={[
          styles.container,
          {
            paddingHorizontal: spacing.screenPadding.horizontal,
            paddingVertical: spacing.screenPadding.vertical,
          },
        ]}
      >
        {/* Header */}
        <View style={[styles.header, { marginBottom: spacing.xl }]}>
          <TouchableOpacity
            onPress={() => navigation.goBack()}
            accessibilityLabel="Go back"
            style={{ marginBottom: spacing.md }}
          >
            <Text style={{ color: colors.neonCyan, fontSize: 16, fontFamily: typography.fontFamily.body }}>
              ← Back
            </Text>
          </TouchableOpacity>
          <Text
            style={{
              color: colors.textPrimary,
              fontSize: 28,
              fontFamily: typography.fontFamily.display,
            }}
          >
            Edit Profile
          </Text>
        </View>

        {/* Form Fields */}
        {fields.map(({ label, field, placeholder, keyboardType }) => (
          <View key={field} style={[styles.fieldRow, { marginBottom: spacing.lg }]}>
            <Text
              style={{
                color: colors.textSecondary,
                fontSize: 13,
                fontFamily: typography.fontFamily.bodyBold,
                marginBottom: spacing.xs,
                textTransform: 'uppercase',
                letterSpacing: 0.8,
              }}
            >
              {label}
            </Text>
            <TextInput
              value={form[field]}
              onChangeText={(v) => handleChange(field, v)}
              placeholder={placeholder}
              placeholderTextColor={colors.textSecondary + '80'}
              keyboardType={keyboardType ?? 'default'}
              accessibilityLabel={label}
              style={[
                styles.input,
                {
                  backgroundColor: colors.card,
                  color: colors.textPrimary,
                  borderColor: colors.textSecondary + '30',
                  fontFamily: typography.fontFamily.body,
                  fontSize: 16,
                  borderRadius: spacing.sm,
                  padding: spacing.md,
                },
              ]}
            />
          </View>
        ))}

        {/* Save Button */}
        <TouchableOpacity
          onPress={handleSave}
          disabled={status === 'loading'}
          accessibilityLabel="Save profile"
          style={[
            styles.saveButton,
            {
              backgroundColor: colors.neonCyan,
              borderRadius: spacing.md,
              padding: spacing.lg,
              marginTop: spacing.md,
              alignItems: 'center',
              opacity: status === 'loading' ? 0.7 : 1,
            },
          ]}
        >
          {status === 'loading' ? (
            <ActivityIndicator color={colors.black} />
          ) : (
            <Text
              style={{
                color: colors.black,
                fontSize: 16,
                fontFamily: typography.fontFamily.bodyBold,
              }}
            >
              Save Changes
            </Text>
          )}
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: { flex: 1 },
  scrollView: { flex: 1 },
  container: {},
  header: {},
  fieldRow: {},
  input: { borderWidth: 1 },
  saveButton: {},
});
