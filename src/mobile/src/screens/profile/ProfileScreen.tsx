/**
 * Profile Screen
 * 
 * User profile, settings, and logout functionality
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  SafeAreaView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useTheme } from '../../hooks/useTheme';
import { useAuthStore, useCurrentUser } from '../../store/authStore';

export const ProfileScreen = () => {
  const { colors, spacing, typography } = useTheme();
  const user = useCurrentUser();
  const logout = useAuthStore((state) => state.logout);

  const handleLogout = () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out?',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Sign Out',
          style: 'destructive',
          onPress: async () => {
            try {
              await logout();
            } catch (error) {
              console.error('Logout error:', error);
              Alert.alert('Error', 'Failed to sign out. Please try again.');
            }
          },
        },
      ],
      { cancelable: true }
    );
  };

  const menuSections = [
    {
      title: 'Account',
      items: [
        { label: 'Edit Profile', icon: '✏️', action: () => {} },
        { label: 'Payment Methods', icon: '💳', action: () => {} },
        { label: 'Subscription Management', icon: '📋', action: () => {} },
      ],
    },
    {
      title: 'Preferences',
      items: [
        { label: 'Notifications', icon: '🔔', action: () => {} },
        { label: 'Settings', icon: '⚙️', action: () => {} },
      ],
    },
    {
      title: 'Support',
      items: [
        { label: 'Help Center', icon: '❓', action: () => {} },
        { label: 'Privacy Policy', icon: '🔒', action: () => {} },
        { label: 'Terms of Service', icon: '📄', action: () => {} },
      ],
    },
  ];

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.black }]}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={[styles.container, { padding: spacing.screenPadding }]}
      >
        {/* Header */}
        <View style={[styles.header, { marginBottom: spacing.xl }]}>
          <Text
            style={[
              styles.title,
              {
                color: colors.textPrimary,
                fontSize: 28,
                fontFamily: typography.fontFamily.display,
                marginBottom: spacing.md,
              },
            ]}
          >
            Profile
          </Text>
        </View>

        {/* User Info Card */}
        <View
          style={[
            styles.userCard,
            {
              backgroundColor: colors.card,
              borderRadius: spacing.md,
              padding: spacing.lg,
              marginBottom: spacing.xl,
            },
          ]}
        >
          {/* Avatar */}
          <View
            style={[
              styles.avatar,
              {
                width: 80,
                height: 80,
                borderRadius: 40,
                backgroundColor: colors.neonCyan + '30',
                justifyContent: 'center',
                alignItems: 'center',
                marginBottom: spacing.md,
              },
            ]}
          >
            <Text style={{ fontSize: 40 }}>
              {user?.full_name?.charAt(0).toUpperCase() || '👤'}
            </Text>
          </View>

          {/* User Details */}
          <Text
            style={[
              styles.userName,
              {
                color: colors.textPrimary,
                fontSize: 24,
                fontFamily: typography.fontFamily.bodyBold,
                textAlign: 'center',
                marginBottom: spacing.xs,
              },
            ]}
          >
            {user?.full_name || 'User'}
          </Text>
          <Text
            style={[
              styles.userEmail,
              {
                color: colors.textSecondary,
                fontSize: 14,
                fontFamily: typography.fontFamily.body,
                textAlign: 'center',
                marginBottom: spacing.xs,
              },
            ]}
          >
            {user?.email}
          </Text>
          {user?.phone && (
            <Text
              style={[
                styles.userPhone,
                {
                  color: colors.textSecondary,
                  fontSize: 14,
                  fontFamily: typography.fontFamily.body,
                  textAlign: 'center',
                },
              ]}
            >
              {user.phone}
            </Text>
          )}
          {user?.business_name && (
            <View
              style={[
                styles.businessBadge,
                {
                  backgroundColor: colors.neonCyan + '20',
                  borderRadius: spacing.sm,
                  paddingHorizontal: spacing.md,
                  paddingVertical: spacing.xs,
                  marginTop: spacing.sm,
                },
              ]}
            >
              <Text
                style={[
                  styles.businessName,
                  {
                    color: colors.neonCyan,
                    fontSize: 12,
                    fontFamily: typography.fontFamily.bodyBold,
                  },
                ]}
              >
                🏢 {user.business_name}
              </Text>
            </View>
          )}
        </View>

        {/* Menu Sections */}
        {menuSections.map((section, sectionIndex) => (
          <View
            key={section.title}
            style={[styles.menuSection, { marginBottom: spacing.xl }]}
          >
            <Text
              style={[
                styles.sectionTitle,
                {
                  color: colors.textSecondary,
                  fontSize: 14,
                  fontFamily: typography.fontFamily.bodyBold,
                  marginBottom: spacing.md,
                  textTransform: 'uppercase',
                  letterSpacing: 1,
                },
              ]}
            >
              {section.title}
            </Text>
            <View
              style={[
                styles.menuCard,
                {
                  backgroundColor: colors.card,
                  borderRadius: spacing.md,
                  overflow: 'hidden',
                },
              ]}
            >
              {section.items.map((item, itemIndex) => (
                <TouchableOpacity
                  key={item.label}
                  style={[
                    styles.menuItem,
                    {
                      padding: spacing.lg,
                      flexDirection: 'row',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      borderBottomWidth:
                        itemIndex < section.items.length - 1 ? 1 : 0,
                      borderBottomColor: colors.textSecondary + '20',
                    },
                  ]}
                  onPress={item.action}
                >
                  <View style={[styles.menuItemLeft, { flexDirection: 'row', alignItems: 'center' }]}>
                    <Text style={{ fontSize: 24, marginRight: spacing.md }}>
                      {item.icon}
                    </Text>
                    <Text
                      style={[
                        styles.menuItemLabel,
                        {
                          color: colors.textPrimary,
                          fontSize: 16,
                          fontFamily: typography.fontFamily.body,
                        },
                      ]}
                    >
                      {item.label}
                    </Text>
                  </View>
                  <Text style={{ fontSize: 20, color: colors.textSecondary }}>
                    →
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        ))}

        {/* Logout Button */}
        <TouchableOpacity
          style={[
            styles.logoutButton,
            {
              backgroundColor: colors.error + '20',
              borderRadius: spacing.md,
              padding: spacing.lg,
              marginBottom: spacing.xl,
              alignItems: 'center',
            },
          ]}
          onPress={handleLogout}
        >
          <Text
            style={[
              styles.logoutButtonText,
              {
                color: colors.error,
                fontSize: 16,
                fontFamily: typography.fontFamily.bodyBold,
              },
            ]}
          >
            Sign Out
          </Text>
        </TouchableOpacity>

        {/* App Info */}
        <View style={[styles.appInfo, { alignItems: 'center', paddingBottom: spacing.xl }]}>
          <Text
            style={[
              styles.appName,
              {
                color: colors.neonCyan,
                fontSize: 20,
                fontFamily: typography.fontFamily.display,
                marginBottom: spacing.xs,
              },
            ]}
          >
            WAOOAW
          </Text>
          <Text
            style={[
              styles.appVersion,
              {
                color: colors.textSecondary,
                fontSize: 12,
                fontFamily: typography.fontFamily.body,
                marginBottom: spacing.xs,
              },
            ]}
          >
            Version 1.0.0
          </Text>
          <Text
            style={[
              styles.appTagline,
              {
                color: colors.textSecondary,
                fontSize: 12,
                fontFamily: typography.fontFamily.body,
                textAlign: 'center',
              },
            ]}
          >
            Agents Earn Your Business
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  container: {},
  header: {},
  title: {},
  userCard: {
    alignItems: 'center',
  },
  avatar: {},
  userName: {},
  userEmail: {},
  userPhone: {},
  businessBadge: {},
  businessName: {},
  menuSection: {},
  sectionTitle: {},
  menuCard: {},
  menuItem: {},
  menuItemLeft: {},
  menuItemLabel: {},
  logoutButton: {},
  logoutButtonText: {},
  appInfo: {},
  appName: {},
  appVersion: {},
  appTagline: {},
});
