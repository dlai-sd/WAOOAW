/**
 * Sign In Screen Tests
 */

import React from "react";
import { render, fireEvent, waitFor } from "@testing-library/react-native";
import { Alert } from "react-native";
import { SignInScreen } from "../src/screens/auth/SignInScreen";
import AuthService from "../src/services/auth.service";
import { useGoogleAuth } from "../src/hooks/useGoogleAuth";

// Mock dependencies
jest.mock("../src/services/auth.service");
jest.mock("../src/hooks/useGoogleAuth");
jest.mock("../src/hooks/useTheme", () => ({
  useTheme: () => ({
    colors: {
      neonCyan: "#00f2fe",
      textPrimary: "#ffffff",
      textSecondary: "#a1a1aa",
      black: "#0a0a0a",
      error: "#ef4444",
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
        display: "SpaceGrotesk_700Bold",
        body: "Inter_400Regular",
        bodyBold: "Inter_600SemiBold",
      },
    },
  }),
}));

// Mock Alert
jest.spyOn(Alert, "alert").mockImplementation(() => {});

const mockUseGoogleAuth = useGoogleAuth as jest.MockedFunction<
  typeof useGoogleAuth
>;

describe("SignInScreen", () => {
  const mockOnSignUpPress = jest.fn();
  const mockOnSignInSuccess = jest.fn();
  const mockPromptAsync = jest.fn();
  const mockReset = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockPromptAsync.mockResolvedValue(undefined);

    // Default mock for useGoogleAuth
    mockUseGoogleAuth.mockReturnValue({
      promptAsync: mockPromptAsync,
      loading: false,
      error: null,
      idToken: null,
      userInfo: null,
      isConfigured: true,
      reset: mockReset,
    });

    (AuthService.loginWithGoogle as jest.Mock).mockResolvedValue({
      id: "user_123",
      email: "test@example.com",
      name: "Test User",
    });
  });

  it("should render correctly", () => {
    const { getByText, getByLabelText, getByTestId, queryByText } = render(<SignInScreen />);

    // Logo is now an Image with accessibilityLabel, not a Text node
    expect(queryByText("WAOOAW")).toBeNull();
    expect(getByLabelText("WAOOAW")).toBeTruthy();
    expect(getByTestId("mobile-signin-screen")).toBeTruthy();
    expect(getByTestId("mobile-google-signin-button")).toBeTruthy();
    expect(getByText("Welcome Back")).toBeTruthy();
    expect(getByText("Agents Earn Your Business")).toBeTruthy();
    expect(getByText("Sign in with Google")).toBeTruthy();
    expect(getByText("Don't have an account?")).toBeTruthy();
    expect(getByText("Sign up")).toBeTruthy();
    expect(getByText("The First AI Agent Marketplace")).toBeTruthy();
  });

  it("should call onSignUpPress when sign up link is pressed", () => {
    const { getByTestId } = render(
      <SignInScreen onSignUpPress={mockOnSignUpPress} />,
    );

    fireEvent.press(getByTestId("mobile-signup-link"));
    expect(mockOnSignUpPress).toHaveBeenCalledTimes(1);
  });

  it("should call promptAsync when Google sign in button is pressed", async () => {
    const { getByText } = render(<SignInScreen />);

    fireEvent.press(getByText("Sign in with Google"));

    await waitFor(() => {
      expect(mockPromptAsync).toHaveBeenCalled();
    });
  });

  it("should handle sign in error from promptAsync", async () => {
    mockPromptAsync.mockRejectedValue(new Error("OAuth initialization failed"));

    const { getByText } = render(<SignInScreen />);

    fireEvent.press(getByText("Sign in with Google"));

    await waitFor(() => {
      expect(mockPromptAsync).toHaveBeenCalled();
      expect(
        getByText("Failed to start sign-in. Please try again."),
      ).toBeTruthy();
    });
  });

  it("should show loading state from hook", () => {
    mockUseGoogleAuth.mockReturnValue({
      promptAsync: mockPromptAsync,
      loading: true,
      error: null,
      idToken: null,
      userInfo: null,
      isConfigured: true,
      reset: mockReset,
    });

    const { getByLabelText } = render(<SignInScreen />);

    const button = getByLabelText("Sign in with Google");
    expect(button.props.accessibilityState.disabled).toBe(true);
  });

  it("should disable sign up link when loading", () => {
    mockUseGoogleAuth.mockReturnValue({
      promptAsync: mockPromptAsync,
      loading: true,
      error: null,
      idToken: null,
      userInfo: null,
      isConfigured: true,
      reset: mockReset,
    });

    const { getByLabelText } = render(
      <SignInScreen onSignUpPress={mockOnSignUpPress} />,
    );

    const signUpButton = getByLabelText("Sign up");
    expect(signUpButton.props.accessibilityState.disabled).toBe(true);
  });
});

describe("SignInScreen - idToken exchange", () => {
  const mockOnSignUpPress = jest.fn();
  const mockOnSignInSuccess = jest.fn();
  const mockPromptAsync = jest.fn();
  const mockReset = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockPromptAsync.mockResolvedValue(undefined);
  });

  it("should exchange idToken via AuthService and call login + onSignInSuccess on success", async () => {
    (AuthService.loginWithGoogle as jest.Mock).mockResolvedValue({
      id: "user_456",
      email: "user@test.com",
      name: "User Test",
    });

    mockUseGoogleAuth.mockReturnValue({
      promptAsync: mockPromptAsync,
      loading: false,
      error: null,
      idToken: "valid-id-token",
      userInfo: null,
      isConfigured: true,
      reset: mockReset,
    });

    render(<SignInScreen onSignInSuccess={mockOnSignInSuccess} />);

    await waitFor(() => {
      expect(AuthService.loginWithGoogle).toHaveBeenCalledWith("valid-id-token");
    });
  });

  it("shows 2FA alert when backend returns 2FA_REQUIRED error", async () => {
    const twoFaError = new Error("2FA required");
    (twoFaError as any).code = "2FA_REQUIRED";
    (AuthService.loginWithGoogle as jest.Mock).mockRejectedValue(twoFaError);

    mockUseGoogleAuth.mockReturnValue({
      promptAsync: mockPromptAsync,
      loading: false,
      error: null,
      idToken: "token-2fa",
      userInfo: null,
      isConfigured: true,
      reset: mockReset,
    });

    render(<SignInScreen />);

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        "2FA Required",
        expect.stringContaining("two-factor"),
        expect.any(Array),
      );
    });
  });

  it("shows error message for generic backend authentication failure", async () => {
    const genericError = new Error("Server error");
    (AuthService.loginWithGoogle as jest.Mock).mockRejectedValue(genericError);

    mockUseGoogleAuth.mockReturnValue({
      promptAsync: mockPromptAsync,
      loading: false,
      error: null,
      idToken: "token-fail",
      userInfo: null,
      isConfigured: true,
      reset: mockReset,
    });

    const { getByText } = render(<SignInScreen />);

    await waitFor(() => {
      expect(getByText("Server error")).toBeTruthy();
    });
  });

  it("does not show error for USER_CANCELLED oauthError", async () => {
    mockUseGoogleAuth.mockReturnValue({
      promptAsync: mockPromptAsync,
      loading: false,
      error: { code: "USER_CANCELLED", message: "User cancelled" } as any,
      idToken: null,
      userInfo: null,
      isConfigured: true,
      reset: mockReset,
    });

    const { queryByText } = render(<SignInScreen />);

    // No error text shown for USER_CANCELLED
    expect(queryByText("User cancelled")).toBeNull();
  });

  it("shows error message for non-cancellation oauthError", async () => {
    mockUseGoogleAuth.mockReturnValue({
      promptAsync: mockPromptAsync,
      loading: false,
      error: { code: "SIGN_IN_ERROR", message: "OAuth network error" } as any,
      idToken: null,
      userInfo: null,
      isConfigured: true,
      reset: mockReset,
    });

    const { getByText } = render(<SignInScreen />);

    await waitFor(() => {
      expect(getByText("OAuth network error")).toBeTruthy();
    });
  });
});
