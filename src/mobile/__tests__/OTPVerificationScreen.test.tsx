/**
 * OTPVerificationScreen Tests
 */

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { Alert } from 'react-native';
import { OTPVerificationScreen } from '../src/screens/auth/OTPVerificationScreen';
import RegistrationService from '../src/services/registration.service';

// Mock dependencies
jest.mock('../src/services/registration.service');
jest.mock('../src/components/OTPInput', () => ({
  OTPInput: ({ onComplete, onChange }: any) => {
    const { View, TextInput } = require('react-native');
    return (
      <View>
        <TextInput
          testID="otp-input"
          onChangeText={(text: string) => {
            onChange?.(text);
            if (text.length === 6) {
              onComplete?.(text);
            }
          }}
        />
      </View>
    );
  },
}));
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

// Mock timers
jest.useFakeTimers();

describe('OTPVerificationScreen', () => {
  const mockOnVerificationSuccess = jest.fn();
  const mockOnBack = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render correctly', () => {
    const { getByText, getByTestId } = render(
      <OTPVerificationScreen
        registrationId="REG-123"
        otpId="OTP-123"
        destinationMasked="t***t@example.com"
      />
    );

    expect(getByText('WAOOAW')).toBeTruthy();
    expect(getByText('Verify Your Account')).toBeTruthy();
    expect(getByText(/Enter the 6-digit code sent to/)).toBeTruthy();
    expect(getByText('t***t@example.com')).toBeTruthy();
    expect(getByTestId('otp-input')).toBeTruthy();
    expect(getByText('Resend Code')).toBeTruthy();
  });

  it('should show back button', () => {
    const { getByLabelText } = render(
      <OTPVerificationScreen
        registrationId="REG-123"
        otpId="OTP-123"
        destinationMasked="t***t@example.com"
        onBack={mockOnBack}
      />
    );

    expect(getByLabelText('Go back')).toBeTruthy();
  });

  it('should call onBack when back button is pressed', () => {
    const { getByLabelText } = render(
      <OTPVerificationScreen
        registrationId="REG-123"
        otpId="OTP-123"
        destinationMasked="t***t@example.com"
        onBack={mockOnBack}
      />
    );

    fireEvent.press(getByLabelText('Go back'));
    expect(mockOnBack).toHaveBeenCalledTimes(1);
  });

  it('should verify OTP when complete code is entered', async () => {
    (RegistrationService.verifyOTP as jest.Mock).mockResolvedValue({
      access_token: 'access-token-123',
      refresh_token: 'refresh-token-123',
      user: {
        customer_id: 'CUST-123',
        email: 'test@example.com',
      },
    });

    const { getByTestId } = render(
      <OTPVerificationScreen
        registrationId="REG-123"
        otpId="OTP-123"
        destinationMasked="t***t@example.com"
        onVerificationSuccess={mockOnVerificationSuccess}
      />
    );

    fireEvent.changeText(getByTestId('otp-input'), '123456');

    await waitFor(() => {
      expect(RegistrationService.verifyOTP).toHaveBeenCalledWith('OTP-123', '123456');
      expect(mockOnVerificationSuccess).toHaveBeenCalled();
    });
  });

  it('should handle invalid OTP error', async () => {
    const error = new (class extends Error {
      code = 'INVALID_OTP';
      constructor() {
        super('Invalid OTP code');
        this.name = 'RegistrationServiceError';
      }
    })();

    (RegistrationService.verifyOTP as jest.Mock).mockRejectedValue(error);

    const { getByTestId, findByText } = render(
      <OTPVerificationScreen
        registrationId="REG-123"
        otpId="OTP-123"
        destinationMasked="t***t@example.com"
      />
    );

    fireEvent.changeText(getByTestId('otp-input'), '123456');

    expect(await findByText('Invalid code. Please try again.')).toBeTruthy();
  });

  it('should handle expired OTP error', async () => {
    const error = new (class extends Error {
      code = 'OTP_EXPIRED';
      constructor() {
        super('OTP has expired');
        this.name = 'RegistrationServiceError';
      }
    })();

    (RegistrationService.verifyOTP as jest.Mock).mockRejectedValue(error);

    const { getByTestId, findByText } = render(
      <OTPVerificationScreen
        registrationId="REG-123"
        otpId="OTP-123"
        destinationMasked="t***t@example.com"
      />
    );

    fireEvent.changeText(getByTestId('otp-input'), '123456');

    expect(await findByText('Code expired. Please request a new one.')).toBeTruthy();
  });

  it('should handle too many attempts error', async () => {
    const error = new (class extends Error {
      code = 'TOO_MANY_ATTEMPTS';
      constructor() {
        super('Too many attempts');
        this.name = 'RegistrationServiceError';
      }
    })();

    (RegistrationService.verifyOTP as jest.Mock).mockRejectedValue(error);

    const { getByTestId, findByText } = render(
      <OTPVerificationScreen
        registrationId="REG-123"
        otpId="OTP-123"
        destinationMasked="t***t@example.com"
      />
    );

    fireEvent.changeText(getByTestId('otp-input'), '123456');

    expect(
      await findByText('Too many attempts. Please request a new code.')
    ).toBeTruthy();
  });

  it('should handle generic verification error', async () => {
    const error = new Error('Network error');

    (RegistrationService.verifyOTP as jest.Mock).mockRejectedValue(error);

    const { getByTestId, findByText } = render(
      <OTPVerificationScreen
        registrationId="REG-123"
        otpId="OTP-123"
        destinationMasked="t***t@example.com"
      />
    );

    fireEvent.changeText(getByTestId('otp-input'), '123456');

    expect(await findByText('Verification failed. Please try again.')).toBeTruthy();
  });

  it('should resend OTP successfully', async () => {
    (RegistrationService.startOTP as jest.Mock).mockResolvedValue({
      otp_id: 'OTP-456',
      channel: 'email',
      destination_masked: 't***t@example.com',
      expires_in_seconds: 300,
    });

    const { getByText, findByText } = render(
      <OTPVerificationScreen
        registrationId="REG-123"
        otpId="OTP-123"
        destinationMasked="t***t@example.com"
      />
    );

    fireEvent.press(getByText('Resend Code'));

    await waitFor(() => {
      expect(RegistrationService.startOTP).toHaveBeenCalledWith('REG-123');
    });
    expect(await findByText('Code sent successfully!')).toBeTruthy();
  });

  it('should resend OTP with channel', async () => {
    (RegistrationService.startOTP as jest.Mock).mockResolvedValue({
      otp_id: 'OTP-456',
      channel: 'sms',
      destination_masked: '+91****3210',
      expires_in_seconds: 300,
    });

    const { getByText } = render(
      <OTPVerificationScreen
        registrationId="REG-123"
        otpId="OTP-123"
        channel="sms"
        destinationMasked="+91****3210"
      />
    );

    fireEvent.press(getByText('Resend Code'));

    await waitFor(() => {
      expect(RegistrationService.startOTP).toHaveBeenCalledWith('REG-123', 'sms');
    });
  });

  it('should handle resend OTP error', async () => {
    const error = new Error('Network error');

    (RegistrationService.startOTP as jest.Mock).mockRejectedValue(error);

    const { getByText, findByText } = render(
      <OTPVerificationScreen
        registrationId="REG-123"
        otpId="OTP-123"
        destinationMasked="t***t@example.com"
      />
    );

    fireEvent.press(getByText('Resend Code'));

    expect(await findByText('Failed to resend code. Please try again.')).toBeTruthy();
  });

  it('should disable resend button during cooldown', async () => {
    (RegistrationService.startOTP as jest.Mock).mockResolvedValue({
      otp_id: 'OTP-456',
      channel: 'email',
      destination_masked: 't***t@example.com',
      expires_in_seconds: 300,
    });

    const { getByText } = render(
      <OTPVerificationScreen
        registrationId="REG-123"
        otpId="OTP-123"
        destinationMasked="t***t@example.com"
      />
    );

    // Press resend
    fireEvent.press(getByText('Resend Code'));

    await waitFor(() => {
      expect(RegistrationService.startOTP).toHaveBeenCalled();
    });

    // Button should be disabled
    const resendButton = getByText(/Resend in/).parent;
    expect(resendButton?.props.accessibilityState.disabled).toBe(true);

    // Fast-forward 10 seconds
    act(() => {
      jest.advanceTimersByTime(10000);
    });

    // Button should still be disabled
    expect(getByText(/Resend in/)).toBeTruthy();

    // Fast-forward remaining 20 seconds
    act(() => {
      jest.advanceTimersByTime(20000);
    });

    // Button should be enabled again
    await waitFor(() => {
      expect(getByText('Resend Code')).toBeTruthy();
    });
  });

  it('should show loading state during verification', async () => {
    (RegistrationService.verifyOTP as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    const { getByTestId } = render(
      <OTPVerificationScreen
        registrationId="REG-123"
        otpId="OTP-123"
        destinationMasked="t***t@example.com"
      />
    );

    fireEvent.changeText(getByTestId('otp-input'), '123456');

    // During verification, should show loading state
    await waitFor(() => {
      expect(RegistrationService.verifyOTP).toHaveBeenCalled();
    });
  });

  it('should disable resend button during verification', async () => {
    (RegistrationService.verifyOTP as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    const { getByTestId, getByText } = render(
      <OTPVerificationScreen
        registrationId="REG-123"
        otpId="OTP-123"
        destinationMasked="t***t@example.com"
      />
    );

    // Start verification
    fireEvent.changeText(getByTestId('otp-input'), '123456');

    // Try to press resend during verification
    fireEvent.press(getByText('Resend Code'));

    // Resend should not be called
    expect(RegistrationService.startOTP).not.toHaveBeenCalled();
  });

  it('should disable back button during verification', async () => {
    (RegistrationService.verifyOTP as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    const { getByTestId, getByLabelText } = render(
      <OTPVerificationScreen
        registrationId="REG-123"
        otpId="OTP-123"
        destinationMasked="t***t@example.com"
        onBack={mockOnBack}
      />
    );

    // Start verification
    fireEvent.changeText(getByTestId('otp-input'), '123456');

    // Try to press back during verification
    fireEvent.press(getByLabelText('Go back'));

    // Callback should not be called
    expect(mockOnBack).not.toHaveBeenCalled();
  });

  it('should clear error when user starts typing', async () => {
    const error = new (class extends Error {
      code = 'INVALID_OTP';
      constructor() {
        super('Invalid OTP code');
        this.name = 'RegistrationServiceError';
      }
    })();

    (RegistrationService.verifyOTP as jest.Mock).mockRejectedValue(error);

    const { getByTestId, findByText, queryByText } = render(
      <OTPVerificationScreen
        registrationId="REG-123"
        otpId="OTP-123"
        destinationMasked="t***t@example.com"
      />
    );

    // Trigger error
    fireEvent.changeText(getByTestId('otp-input'), '123456');
    expect(await findByText('Invalid code. Please try again.')).toBeTruthy();

    // Start typing new code
    fireEvent.changeText(getByTestId('otp-input'), '1');

    // Error should clear
    await waitFor(() => {
      expect(queryByText('Invalid code. Please try again.')).toBeNull();
    });
  });
});
