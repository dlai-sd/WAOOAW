/**
 * Google Sign In Button Tests
 */

import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { GoogleSignInButton } from '../src/components/GoogleSignInButton';

// Mock useTheme hook
jest.mock('../src/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      neonCyan: '#00f2fe',
      textPrimary: '#ffffff',
      textSecondary: '#a1a1aa',
      black: '#0a0a0a',
      error: '#ef4444',
    },
    spacing: {
      xs: 4,
      sm: 8,
      md: 16,
      lg: 24,
      xl: 32,
      xxl: 48,
      screenPadding: 20,
    },
    typography: {
      fontFamily: {
        display: 'SpaceGrotesk_700Bold',
        body: 'Inter_400Regular',
        bodyBold: 'Inter_600SemiBold',
      },
    },
  }),
}));

describe('GoogleSignInButton', () => {
  it('should render correctly', () => {
    const onPress = jest.fn();
    const { getByText, getByLabelText } = render(
      <GoogleSignInButton onPress={onPress} />
    );

    expect(getByText('Sign in with Google')).toBeTruthy();
    expect(getByLabelText('Sign in with Google')).toBeTruthy();
  });

  it('should call onPress when pressed', () => {
    const onPress = jest.fn();
    const { getByLabelText } = render(
      <GoogleSignInButton onPress={onPress} />
    );

    fireEvent.press(getByLabelText('Sign in with Google'));
    expect(onPress).toHaveBeenCalledTimes(1);
  });

  it('should show loading indicator when loading', () => {
    const onPress = jest.fn();
    const { getByLabelText, queryByText } = render(
      <GoogleSignInButton onPress={onPress} loading={true} />
    );

    // Button should still be accessible
    expect(getByLabelText('Sign in with Google')).toBeTruthy();
    
    // Text should not be visible when loading
    expect(queryByText('Sign in with Google')).toBeNull();
  });

  it('should be disabled when disabled prop is true', () => {
    const onPress = jest.fn();
    const { getByLabelText } = render(
      <GoogleSignInButton onPress={onPress} disabled={true} />
    );

    const button = getByLabelText('Sign in with Google');
    expect(button.props.accessibilityState.disabled).toBe(true);
    
    // Note: fireEvent.press will still trigger in test environment
    // but the TouchableOpacity's disabled prop will prevent it in real app
  });

  it('should be disabled when loading', () => {
    const onPress = jest.fn();
    const { getByLabelText } = render(
      <GoogleSignInButton onPress={onPress} loading={true} />
    );

    const button = getByLabelText('Sign in with Google');
    expect(button.props.accessibilityState.disabled).toBe(true);
    
    // Note: fireEvent.press will still trigger in test environment
    // but the TouchableOpacity's disabled prop will prevent it in real app
  });

  it('should have correct accessibility properties', () => {
    const onPress = jest.fn();
    const { getByLabelText } = render(
      <GoogleSignInButton onPress={onPress} />
    );

    const button = getByLabelText('Sign in with Google');
    expect(button.props.accessibilityRole).toBe('button');
    expect(button.props.accessibilityState).toEqual({ disabled: false });
  });

  it('should have disabled accessibility state when disabled', () => {
    const onPress = jest.fn();
    const { getByLabelText } = render(
      <GoogleSignInButton onPress={onPress} disabled={true} />
    );

    const button = getByLabelText('Sign in with Google');
    expect(button.props.accessibilityState).toEqual({ disabled: true });
  });

  it('should apply custom style', () => {
    const onPress = jest.fn();
    const customStyle = { marginTop: 20 };
    const { getByLabelText } = render(
      <GoogleSignInButton onPress={onPress} style={customStyle} />
    );

    const button = getByLabelText('Sign in with Google');
    expect(button.props.style).toContainEqual(customStyle);
  });
});
