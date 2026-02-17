/**
 * SignUpScreen Tests
 */

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { Alert } from 'react-native';
import { SignUpScreen } from '../src/screens/auth/SignUpScreen';
import RegistrationService from '../src/services/registration.service';

// Mock dependencies
jest.mock('../src/services/registration.service');
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

// Mock Alert
jest.spyOn(Alert, 'alert').mockImplementation(() => {});

describe('SignUpScreen', () => {
  const mockOnSignInPress = jest.fn();
  const mockOnRegistrationSuccess = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render correctly', () => {
    const { getByText, getByLabelText } = render(<SignUpScreen />);

    expect(getByText('WAOOAW')).toBeTruthy();
    expect(getByText('Create Account')).toBeTruthy();
    expect(getByText('Join the AI Agent Marketplace')).toBeTruthy();
    expect(getByLabelText('Full Name')).toBeTruthy();
    expect(getByLabelText('Email')).toBeTruthy();
    expect(getByLabelText('Phone')).toBeTruthy();
    expect(getByLabelText('Business Name')).toBeTruthy();
    expect(getByText('Sign Up')).toBeTruthy();
    expect(getByText('Already have an account?')).toBeTruthy();
    expect(getByText('Sign in')).toBeTruthy();
  });

  it('should call onSignInPress when sign in link is pressed', () => {
    const { getByText } = render(
      <SignUpScreen onSignInPress={mockOnSignInPress} />
    );

    fireEvent.press(getByText('Sign in'));
    expect(mockOnSignInPress).toHaveBeenCalledTimes(1);
  });

  it('should show validation errors for empty fields', async () => {
    const { getByText, findByText } = render(<SignUpScreen />);

    fireEvent.press(getByText('Sign Up'));

    await waitFor(async () => {
      expect(await findByText('Full name is required')).toBeTruthy();
      expect(await findByText('Email is required')).toBeTruthy();
      expect(await findByText('Phone is required')).toBeTruthy();
    });

    expect(RegistrationService.registerAndStartOTP).not.toHaveBeenCalled();
  });

  it('should show validation error for invalid email', async () => {
    const { getByLabelText, getByText, findByText } = render(<SignUpScreen />);

    fireEvent.changeText(getByLabelText('Full Name'), 'Test User');
    fireEvent.changeText(getByLabelText('Email'), 'invalid-email');
    fireEvent.changeText(getByLabelText('Phone'), '+919876543210');

    fireEvent.press(getByText('Sign Up'));

    await waitFor(async () => {
      expect(await findByText('Invalid email format')).toBeTruthy();
    });

    expect(RegistrationService.registerAndStartOTP).not.toHaveBeenCalled();
  });

  it('should show validation error for invalid phone', async () => {
    const { getByLabelText, getByText, findByText } = render(<SignUpScreen />);

    fireEvent.changeText(getByLabelText('Full Name'), 'Test User');
    fireEvent.changeText(getByLabelText('Email'), 'test@example.com');
    fireEvent.changeText(getByLabelText('Phone'), '123'); // Invalid

    fireEvent.press(getByText('Sign Up'));

    await waitFor(async () => {
      expect(await findByText(/Invalid phone format/)).toBeTruthy();
    });

    expect(RegistrationService.registerAndStartOTP).not.toHaveBeenCalled();
  });

  it('should show validation error for short name', async () => {
    const { getByLabelText, getByText, findByText } = render(<SignUpScreen />);

    fireEvent.changeText(getByLabelText('Full Name'), 'T');
    fireEvent.changeText(getByLabelText('Email'), 'test@example.com');
    fireEvent.changeText(getByLabelText('Phone'), '+919876543210');

    fireEvent.press(getByText('Sign Up'));

    await waitFor(async () => {
      expect(await findByText('Name must be at least 2 characters')).toBeTruthy();
    });

    expect(RegistrationService.registerAndStartOTP).not.toHaveBeenCalled();
  });

  it('should clear field error when user types', async () => {
    const { getByLabelText, getByText, queryByText, findByText } = render(
      <SignUpScreen />
    );

    // Trigger validation error
    fireEvent.press(getByText('Sign Up'));
    await waitFor(async () => {
      expect(await findByText('Email is required')).toBeTruthy();
    });

    // Start typing
    fireEvent.changeText(getByLabelText('Email'), 'test@example.com');

    // Error should clear
    await waitFor(() => {
      expect(queryByText('Email is required')).toBeNull();
    });
  });

  it('should successfully register with required fields', async () => {
    (RegistrationService.registerAndStartOTP as jest.Mock).mockResolvedValue({
      registration: {
        registration_id: 'REG-123',
        email: 'test@example.com',
        phone: '+919876543210',
      },
      otp: {
        otp_id: 'OTP-123',
        channel: 'email',
        destination_masked: 't***t@example.com',
        expires_in_seconds: 300,
      },
    });

    const { getByLabelText, getByText } = render(
      <SignUpScreen onRegistrationSuccess={mockOnRegistrationSuccess} />
    );

    fireEvent.changeText(getByLabelText('Full Name'), 'Test User');
    fireEvent.changeText(getByLabelText('Email'), 'test@example.com');
    fireEvent.changeText(getByLabelText('Phone'), '+919876543210');

    fireEvent.press(getByText('Sign Up'));

    await waitFor(() => {
      expect(RegistrationService.registerAndStartOTP).toHaveBeenCalledWith(
        {
          fullName: 'Test User',
          email: 'test@example.com',
          phone: '+919876543210',
          businessName: undefined,
        }
      );
      expect(mockOnRegistrationSuccess).toHaveBeenCalledWith('REG-123', 'OTP-123');
    });
  });

  it('should successfully register with all fields', async () => {
    (RegistrationService.registerAndStartOTP as jest.Mock).mockResolvedValue({
      registration: {
        registration_id: 'REG-123',
        email: 'test@example.com',
        phone: '+919876543210',
      },
      otp: {
        otp_id: 'OTP-123',
        channel: 'email',
        destination_masked: 't***t@example.com',
        expires_in_seconds: 300,
      },
    });

    const { getByLabelText, getByText } = render(
      <SignUpScreen onRegistrationSuccess={mockOnRegistrationSuccess} />
    );

    fireEvent.changeText(getByLabelText('Full Name'), 'Test User');
    fireEvent.changeText(getByLabelText('Email'), 'test@example.com');
    fireEvent.changeText(getByLabelText('Phone'), '+919876543210');
    fireEvent.changeText(getByLabelText('Business Name'), 'ACME Inc');

    fireEvent.press(getByText('Sign Up'));

    await waitFor(() => {
      expect(RegistrationService.registerAndStartOTP).toHaveBeenCalledWith(
        {
          fullName: 'Test User',
          email: 'test@example.com',
          phone: '+919876543210',
          businessName: 'ACME Inc',
        }
      );
      expect(mockOnRegistrationSuccess).toHaveBeenCalledWith('REG-123', 'OTP-123');
    });
  });

  it('should format phone number with + prefix', async () => {
    (RegistrationService.registerAndStartOTP as jest.Mock).mockResolvedValue({
      registration: {
        registration_id: 'REG-123',
        email: 'test@example.com',
        phone: '+919876543210',
      },
      otp: {
        otp_id: 'OTP-123',
        channel: 'email',
        destination_masked: 't***t@example.com',
        expires_in_seconds: 300,
      },
    });

    const { getByLabelText, getByText } = render(<SignUpScreen />);

    fireEvent.changeText(getByLabelText('Full Name'), 'Test User');
    fireEvent.changeText(getByLabelText('Email'), 'test@example.com');
    fireEvent.changeText(getByLabelText('Phone'), '919876543210'); // Without +

    fireEvent.press(getByText('Sign Up'));

    await waitFor(() => {
      expect(RegistrationService.registerAndStartOTP).toHaveBeenCalledWith(
        expect.objectContaining({
          phone: '+919876543210', // Should add +
        })
      );
    });
  });

  it('should handle email already registered error', async () => {
    const error = new (class extends Error {
      code = 'EMAIL_ALREADY_REGISTERED';
      constructor() {
        super('Email already registered. Please sign in.');
        this.name = 'RegistrationServiceError';
      }
    })();

    (RegistrationService.registerAndStartOTP as jest.Mock).mockRejectedValue(error);

    const { getByLabelText, getByText, findByText } = render(<SignUpScreen />);

    fireEvent.changeText(getByLabelText('Full Name'), 'Test User');
    fireEvent.changeText(getByLabelText('Email'), 'test@example.com');
    fireEvent.changeText(getByLabelText('Phone'), '+919876543210');

    fireEvent.press(getByText('Sign Up'));

    await waitFor(async () => {
      expect(await findByText('Email already registered')).toBeTruthy();
      expect(
        await findByText('This email is already registered. Please sign in.')
      ).toBeTruthy();
    });
  });

  it('should handle phone already registered error', async () => {
    const error = new (class extends Error {
      code = 'PHONE_ALREADY_REGISTERED';
      constructor() {
        super('Phone already registered. Please sign in.');
        this.name = 'RegistrationServiceError';
      }
    })();

    (RegistrationService.registerAndStartOTP as jest.Mock).mockRejectedValue(error);

    const { getByLabelText, getByText, findByText } = render(<SignUpScreen />);

    fireEvent.changeText(getByLabelText('Full Name'), 'Test User');
    fireEvent.changeText(getByLabelText('Email'), 'test@example.com');
    fireEvent.changeText(getByLabelText('Phone'), '+919876543210');

    fireEvent.press(getByText('Sign Up'));

    await waitFor(async () => {
      expect(await findByText('Phone already registered')).toBeTruthy();
      expect(
        await findByText('This phone is already registered. Please sign in.')
      ).toBeTruthy();
    });
  });

  it('should handle generic registration error', async () => {
    const error = new Error('Network error');

    (RegistrationService.registerAndStartOTP as jest.Mock).mockRejectedValue(error);

    const { getByLabelText, getByText, findByText } = render(<SignUpScreen />);

    fireEvent.changeText(getByLabelText('Full Name'), 'Test User');
    fireEvent.changeText(getByLabelText('Email'), 'test@example.com');
    fireEvent.changeText(getByLabelText('Phone'), '+919876543210');

    fireEvent.press(getByText('Sign Up'));

    await waitFor(async () => {
      expect(await findByText('Registration failed. Please try again.')).toBeTruthy();
    });
  });

  it('should show loading state during registration', async () => {
    (RegistrationService.registerAndStartOTP as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    const { getByLabelText, getByText, getByAccessibilityState } = render(
      <SignUpScreen />
    );

    fireEvent.changeText(getByLabelText('Full Name'), 'Test User');
    fireEvent.changeText(getByLabelText('Email'), 'test@example.com');
    fireEvent.changeText(getByLabelText('Phone'), '+919876543210');

    fireEvent.press(getByText('Sign Up'));

    // Button should be disabled during loading
    await waitFor(() => {
      const button = getByText('Sign Up').parent;
      expect(button?.props.accessibilityState.disabled).toBe(true);
    });
  });

  it('should disable sign in link during registration', async () => {
    (RegistrationService.registerAndStartOTP as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    const { getByLabelText, getByText } = render(
      <SignUpScreen onSignInPress={mockOnSignInPress} />
    );

    fireEvent.changeText(getByLabelText('Full Name'), 'Test User');
    fireEvent.changeText(getByLabelText('Email'), 'test@example.com');
    fireEvent.changeText(getByLabelText('Phone'), '+919876543210');

    fireEvent.press(getByText('Sign Up'));

    // Try to press sign in link during loading
    fireEvent.press(getByText('Sign in'));

    // Should not call callback during registration
    expect(mockOnSignInPress).not.toHaveBeenCalled();
  });
});
