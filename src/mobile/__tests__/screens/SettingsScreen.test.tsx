/**
 * SettingsScreen Tests
 */

import React from 'react';
import { Alert } from 'react-native';
import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { SettingsScreen } from '@/screens/profile/SettingsScreen';

// Mock hooks
const mockLogout = jest.fn();
jest.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      black: '#0a0a0a', card: '#18181b', textPrimary: '#fff', textSecondary: '#a1a1aa',
      neonCyan: '#00f2fe', border: '#333', error: '#ef4444',
    },
    spacing: {
      xs: 4, sm: 8, md: 16, lg: 24, xl: 32,
      screenPadding: { horizontal: 20 },
    },
    typography: { fontFamily: { display: 'SpaceGrotesk_700Bold', body: 'Inter_400Regular', bodyBold: 'Inter_600SemiBold' } },
  }),
}));

jest.mock('../../src/store/authStore', () => ({
  useAuthStore: (selector: any) => selector({ logout: mockLogout }),
}));

const mockNavigate = jest.fn();
const mockGoBack = jest.fn();

const mockNavigation = { navigate: mockNavigate, goBack: mockGoBack } as any;

describe('SettingsScreen', () => {
  beforeEach(() => jest.clearAllMocks());

  it('renders settings screen with all sections', () => {
    const { getByText } = render(<SettingsScreen navigation={mockNavigation} route={{} as any} />);
    expect(getByText('Settings')).toBeTruthy();
    expect(getByText(/Manage Notifications/)).toBeTruthy();
    expect(getByText(/Privacy Policy/)).toBeTruthy();
    expect(getByText(/Terms of Service/)).toBeTruthy();
    expect(getByText('Sign Out')).toBeTruthy();
  });

  it('navigates back on Back press', () => {
    const { getByText } = render(<SettingsScreen navigation={mockNavigation} route={{} as any} />);
    fireEvent.press(getByText('← Back'));
    expect(mockGoBack).toHaveBeenCalled();
  });

  it('navigates to Notifications screen', () => {
    const { getByText } = render(<SettingsScreen navigation={mockNavigation} route={{} as any} />);
    fireEvent.press(getByText(/Manage Notifications/));
    expect(mockNavigate).toHaveBeenCalledWith('Notifications');
  });

  it('navigates to PrivacyPolicy screen', () => {
    const { getByText } = render(<SettingsScreen navigation={mockNavigation} route={{} as any} />);
    fireEvent.press(getByText(/Privacy Policy/));
    expect(mockNavigate).toHaveBeenCalledWith('PrivacyPolicy');
  });

  it('navigates to TermsOfService screen', () => {
    const { getByText } = render(<SettingsScreen navigation={mockNavigation} route={{} as any} />);
    fireEvent.press(getByText(/Terms of Service/));
    expect(mockNavigate).toHaveBeenCalledWith('TermsOfService');
  });

  it('shows sign out confirmation alert', () => {
    const alertSpy = jest.spyOn(Alert, 'alert');
    const { getByText } = render(<SettingsScreen navigation={mockNavigation} route={{} as any} />);
    fireEvent.press(getByText('Sign Out'));
    expect(alertSpy).toHaveBeenCalledWith(
      'Sign Out',
      'Are you sure you want to sign out?',
      expect.any(Array),
      expect.any(Object),
    );
  });

  it('calls logout when Sign Out is confirmed', async () => {
    mockLogout.mockResolvedValue(undefined);
    let signOutHandler: () => void = () => {};
    jest.spyOn(Alert, 'alert').mockImplementationOnce((_title, _msg, buttons) => {
      const confirmBtn = (buttons as any[]).find((b) => b.text === 'Sign Out');
      signOutHandler = confirmBtn.onPress;
    });
    const { getByText } = render(<SettingsScreen navigation={mockNavigation} route={{} as any} />);
    fireEvent.press(getByText('Sign Out'));
    await waitFor(() => signOutHandler());
    expect(mockLogout).toHaveBeenCalled();
  });

  it('handles logout error gracefully', async () => {
    mockLogout.mockRejectedValue(new Error('Logout failed'));
    let signOutHandler: () => void = () => {};
    jest.spyOn(Alert, 'alert').mockImplementationOnce((_title, _msg, buttons) => {
      const confirmBtn = (buttons as any[]).find((b) => b.text === 'Sign Out');
      signOutHandler = confirmBtn.onPress;
    });
    const { getByText } = render(<SettingsScreen navigation={mockNavigation} route={{} as any} />);
    fireEvent.press(getByText('Sign Out'));
    // Should not throw even on error
    await waitFor(() => expect(() => signOutHandler()).not.toThrow());
  });
});
