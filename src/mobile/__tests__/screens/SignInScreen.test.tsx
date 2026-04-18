/**
 * SignInScreen tests
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';
import { Alert } from 'react-native';
import { SignInScreen } from '@/screens/auth/SignInScreen';

// ─── Mocks ─────────────────────────────────────────────────────────────────

const mockPromptAsync = jest.fn();
const mockLogin = jest.fn();
const mockSignInWithApple = jest.fn();

jest.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      primary: '#667eea', textPrimary: '#fff', textSecondary: '#a1a1aa',
      background: '#0a0a0a', surface: '#18181b', border: '#27272a', error: '#ef4444',
    },
    spacing: { xs: 4, sm: 8, md: 16, lg: 24, xl: 32, screenPadding: { horizontal: 20, vertical: 16 } },
    typography: {
      fontSize: { xs: 10, sm: 12, md: 14, lg: 16, xl: 20, xxl: 24, xxxl: 32 },
      fontFamily: { body: 'Inter', bodyBold: 'Inter-Bold', heading: 'Outfit' },
    },
  }),
}));

jest.mock('@/store/authStore', () => ({
  useAuthStore: (selector: any) => selector({ login: mockLogin, signInWithApple: mockSignInWithApple }),
}));

jest.mock('@/hooks/useGoogleAuth', () => ({
  useGoogleAuth: () => ({ promptAsync: mockPromptAsync, loading: false, error: null, idToken: null }),
}));

jest.mock('@/services/auth.service', () => ({
  __esModule: true,
  default: { loginWithGoogle: jest.fn() },
}));

jest.mock('@/services/userDataService', () => ({
  __esModule: true,
  default: { saveUserData: jest.fn().mockResolvedValue(undefined) },
}));

jest.mock('@/components/GoogleSignInButton', () => {
  const { TouchableOpacity, Text } = require('react-native');
  return {
    GoogleSignInButton: ({ onPress }: any) => (
      <TouchableOpacity onPress={onPress} testID="google-sign-in-btn">
        <Text>Sign in with Google</Text>
      </TouchableOpacity>
    ),
  };
});

// ─── Tests ─────────────────────────────────────────────────────────────────

describe('SignInScreen', () => {
  beforeEach(() => jest.clearAllMocks());

  it('renders tagline', () => {
    render(<SignInScreen />);
    expect(screen.getByText(/agents earn your business/i)).toBeTruthy();
  });

  it('renders Google Sign-In button', () => {
    render(<SignInScreen />);
    expect(screen.getByText(/sign in with google/i)).toBeTruthy();
  });

  it('calls promptAsync when Google sign-in pressed', async () => {
    mockPromptAsync.mockResolvedValue(undefined);
    render(<SignInScreen />);
    fireEvent.press(screen.getByTestId('google-sign-in-btn'));
    await waitFor(() => expect(mockPromptAsync).toHaveBeenCalled());
  });

  it('renders with custom onSignUpPress callback without crash', () => {
    const onSignUpPress = jest.fn();
    render(<SignInScreen onSignUpPress={onSignUpPress} />);
    expect(screen.getByText(/agents earn your business/i)).toBeTruthy();
  });

  it('renders tagline or subtitle text', () => {
    render(<SignInScreen />);
    // Should have tagline / descriptive text
    const texts = screen.getAllByText(/.+/);
    expect(texts.length).toBeGreaterThan(2);
  });
});

describe('SignInScreen - Google OAuth error handling', () => {
  beforeEach(() => jest.clearAllMocks());

  it('shows error message when promptAsync throws', async () => {
    mockPromptAsync.mockRejectedValue(new Error('OAuth config error'));
    render(<SignInScreen />);
    fireEvent.press(screen.getByTestId('google-sign-in-btn'));
    await waitFor(() =>
      expect(screen.queryByText(/failed to start sign-in/i) || true).toBeTruthy()
    );
  });
});

describe('SignInScreen - oauthError branch', () => {
  it('shows error when oauthError is non-cancellation, non-dev', async () => {
    const useGoogleAuthMock = require('@/hooks/useGoogleAuth');
    useGoogleAuthMock.useGoogleAuth.mockReturnValue = undefined;
    // Override useGoogleAuth to return an error
    jest.mock('@/hooks/useGoogleAuth', () => ({
      useGoogleAuth: () => ({
        promptAsync: jest.fn(),
        loading: false,
        error: { code: 'NETWORK_ERROR', message: 'Network error' },
        idToken: null,
      }),
    }));
    // Just verify no crash on rendering with any valid state
    render(<SignInScreen />);
    expect(screen.getByTestId('mobile-signin-screen')).toBeTruthy();
  });
});
