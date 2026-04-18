/**
 * HelpCenterScreen Tests
 */

import React from 'react';
import { Linking } from 'react-native';
import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { render, fireEvent } from '@testing-library/react-native';
import { HelpCenterScreen } from '@/screens/profile/HelpCenterScreen';

jest.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      black: '#0a0a0a', textPrimary: '#fff', textSecondary: '#a1a1aa',
      neonCyan: '#00f2fe', border: '#333',
    },
    spacing: {
      xs: 4, sm: 8, md: 16, lg: 24, xl: 32,
      screenPadding: { horizontal: 20 },
    },
    typography: { fontFamily: { display: 'SpaceGrotesk_700Bold', body: 'Inter_400Regular', bodyBold: 'Inter_600SemiBold' } },
  }),
}));

const mockGoBack = jest.fn();
const mockNavigation = { goBack: mockGoBack } as any;

describe('HelpCenterScreen', () => {
  beforeEach(() => jest.clearAllMocks());

  it('renders FAQ items', () => {
    const { getByText } = render(<HelpCenterScreen navigation={mockNavigation} route={{} as any} />);
    expect(getByText('Help Center')).toBeTruthy();
    expect(getByText('What is a 7-day trial?')).toBeTruthy();
    expect(getByText('How do I cancel my subscription?')).toBeTruthy();
  });

  it('navigates back on Back press', () => {
    const { getByText } = render(<HelpCenterScreen navigation={mockNavigation} route={{} as any} />);
    fireEvent.press(getByText('← Back'));
    expect(mockGoBack).toHaveBeenCalled();
  });

  it('expands FAQ item when pressed', () => {
    const { getByText, queryByText } = render(<HelpCenterScreen navigation={mockNavigation} route={{} as any} />);
    // Answer not visible initially
    expect(queryByText(/You get full access/)).toBeNull();
    fireEvent.press(getByText('What is a 7-day trial?'));
    expect(getByText(/You get full access/)).toBeTruthy();
  });

  it('collapses FAQ item when pressed again', () => {
    const { getByText, queryByText } = render(<HelpCenterScreen navigation={mockNavigation} route={{} as any} />);
    // Expand
    fireEvent.press(getByText('What is a 7-day trial?'));
    expect(getByText(/You get full access/)).toBeTruthy();
    // Collapse (press same item again)
    fireEvent.press(getByText('What is a 7-day trial?'));
    expect(queryByText(/You get full access/)).toBeNull();
  });

  it('expands a different FAQ item', () => {
    const { getByText } = render(<HelpCenterScreen navigation={mockNavigation} route={{} as any} />);
    fireEvent.press(getByText('How do I cancel my subscription?'));
    expect(getByText(/Go to Profile → Subscription Management/)).toBeTruthy();
  });

  it('opens support email on Contact Support press', () => {
    const openURLSpy = jest.spyOn(Linking, 'openURL').mockResolvedValue(undefined as any);
    const { getByText } = render(<HelpCenterScreen navigation={mockNavigation} route={{} as any} />);
    fireEvent.press(getByText(/Contact Support/));
    expect(openURLSpy).toHaveBeenCalledWith('mailto:support@waooaw.com');
  });
});
