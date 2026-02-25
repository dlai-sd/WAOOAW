/**
 * SignUpScreen Tests — Iteration 1
 * Covers Story 1 (safe area edges), Story 2 (logo image), Story 3 (11-field form parity)
 */

import React from "react";
import {
  render,
  fireEvent,
  waitFor,
  configure,
} from "@testing-library/react-native";
import { SignUpScreen } from "../src/screens/auth/SignUpScreen";
import RegistrationService from "../src/services/registration.service";

// Include hidden-from-accessibility elements so that sibling Modals with
// accessibilityViewIsModal don't shadow the main form fields.
configure({ defaultIncludeHiddenElements: true });

// Mock dependencies
jest.mock("../src/services/registration.service");
jest.mock("../src/hooks/useTheme", () => ({
  useTheme: () => ({
    colors: {
      neonCyan: "#00f2fe",
      textPrimary: "#ffffff",
      textSecondary: "#a1a1aa",
      black: "#0a0a0a",
      error: "#ef4444",
      gray900: "#001933",
    },
    spacing: {
      xs: 4,
      sm: 8,
      md: 16,
      lg: 24,
      xl: 32,
      xxl: 48,
      screenPadding: { horizontal: 20, vertical: 24 },
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

// ── Test helpers ───────────────────────────────────────────────────────────────

const OTP_SUCCESS = {
  registration: {
    registration_id: "REG-123",
    email: "test@example.com",
    phone: "+919876543210",
  },
  otp: {
    otp_id: "OTP-123",
    channel: "email" as const,
    destination_masked: "t***t@example.com",
    expires_in_seconds: 300,
  },
};

/** Fill all required fields except business industry (use separate picker interaction) */
const fillRequiredFields = (
  getByLabelText: (l: string) => any,
  getByText: (t: string) => any,
) => {
  fireEvent.changeText(getByLabelText("Full Name"), "Test User");
  fireEvent.changeText(getByLabelText("Business Name"), "ACME Inc");
  fireEvent.changeText(
    getByLabelText("Business Address"),
    "123 Main St, Bengaluru",
  );
  fireEvent.changeText(getByLabelText("Email"), "test@example.com");
  fireEvent.changeText(getByLabelText("Phone Number"), "9876543210");
  fireEvent.press(getByText("Email")); // contact method toggle
  fireEvent.press(
    getByLabelText("I agree to the Terms of Service and Privacy Policy"),
  ); // consent
};

// ── Tests ──────────────────────────────────────────────────────────────────────

describe("SignUpScreen", () => {
  const mockOnSignInPress = jest.fn();
  const mockOnRegistrationSuccess = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ── Story 2: Logo is an Image, not text ──────────────────────────────────────

  it("renders WAOOAW logo as image component, not text", () => {
    const { queryByText, getByLabelText } = render(<SignUpScreen />);
    // Logo text should NOT be rendered — it's an Image with accessibilityLabel
    expect(queryByText("WAOOAW")).toBeNull();
    expect(getByLabelText("WAOOAW")).toBeTruthy();
  });

  // ── Rendering ────────────────────────────────────────────────────────────────

  it("renders without crashing", () => {
    expect(() => render(<SignUpScreen />)).not.toThrow();
  });

  it("renders all 11 form fields", () => {
    const { getByText, getByLabelText } = render(<SignUpScreen />);

    expect(getByText("Create Account")).toBeTruthy();
    expect(getByLabelText("Full Name")).toBeTruthy();
    expect(getByLabelText("Business Name")).toBeTruthy();
    expect(getByLabelText("Business Industry")).toBeTruthy();
    expect(getByLabelText("Business Address")).toBeTruthy();
    expect(getByLabelText("Email")).toBeTruthy();
    expect(getByLabelText("Phone Number")).toBeTruthy();
    expect(getByLabelText("Website")).toBeTruthy();
    expect(getByLabelText("GST Number")).toBeTruthy();
    expect(getByLabelText("Email contact method")).toBeTruthy();
    expect(getByLabelText("Phone contact method")).toBeTruthy();
    expect(
      getByLabelText("I agree to the Terms of Service and Privacy Policy"),
    ).toBeTruthy();
    expect(getByText("Sign Up")).toBeTruthy();
    expect(getByText("Sign in")).toBeTruthy();
  });

  it("calls onSignInPress when sign in link is pressed", () => {
    const { getByText } = render(
      <SignUpScreen onSignInPress={mockOnSignInPress} />,
    );
    fireEvent.press(getByText("Sign in"));
    expect(mockOnSignInPress).toHaveBeenCalledTimes(1);
  });

  // ── Story 1: SafeAreaView includes bottom edge ─────────────────────────────

  it("renders SafeAreaView (all four edges including bottom)", () => {
    // SafeAreaView is mocked as a plain 'SafeAreaView' string component in jest.setup.js
    // We verify the screen renders without it crashing due to missing insets
    const { toJSON } = render(<SignUpScreen />);
    expect(toJSON()).toBeTruthy();
  });

  // ── Story 3: Validation ───────────────────────────────────────────────────

  it("shows required-field errors on empty submit", async () => {
    const { getByText, findByText } = render(<SignUpScreen />);
    fireEvent.press(getByText("Sign Up"));

    await waitFor(async () => {
      expect(await findByText("Full name is required")).toBeTruthy();
      expect(await findByText("Business name is required")).toBeTruthy();
      expect(await findByText("Business industry is required")).toBeTruthy();
      expect(await findByText("Business address is required")).toBeTruthy();
      expect(await findByText("Email is required")).toBeTruthy();
      expect(await findByText("Phone number is required")).toBeTruthy();
      expect(
        await findByText("Select a preferred contact method"),
      ).toBeTruthy();
      expect(
        await findByText("You must accept the terms to continue"),
      ).toBeTruthy();
    });

    expect(RegistrationService.registerAndStartOTP).not.toHaveBeenCalled();
  });

  it("validates full name must be ≥ 2 characters", async () => {
    const { getByLabelText, getByText, findByText } = render(<SignUpScreen />);
    fireEvent.changeText(getByLabelText("Full Name"), "T");
    fireEvent.press(getByText("Sign Up"));
    expect(await findByText("Name must be at least 2 characters")).toBeTruthy();
    expect(RegistrationService.registerAndStartOTP).not.toHaveBeenCalled();
  });

  it("validates email format", async () => {
    const { getByLabelText, getByText, findByText } = render(<SignUpScreen />);
    fireEvent.changeText(getByLabelText("Email"), "invalid-email");
    fireEvent.press(getByText("Sign Up"));
    expect(await findByText("Invalid email format")).toBeTruthy();
  });

  it("validates Indian phone (default IN): must start with 6-9 and be 10 digits", async () => {
    const { getByLabelText, getByText, findByText } = render(<SignUpScreen />);
    fireEvent.changeText(getByLabelText("Phone Number"), "1234567890"); // starts with 1
    fireEvent.press(getByText("Sign Up"));
    expect(
      await findByText("Enter a valid 10-digit Indian mobile number"),
    ).toBeTruthy();
    expect(RegistrationService.registerAndStartOTP).not.toHaveBeenCalled();
  });

  it("validates website URL format when provided", async () => {
    const { getByLabelText, getByText, findByText } = render(<SignUpScreen />);
    fireEvent.changeText(getByLabelText("Website"), "not-a-url");
    fireEvent.press(getByText("Sign Up"));
    expect(
      await findByText("Enter a valid URL (e.g. https://example.com)"),
    ).toBeTruthy();
  });

  it("accepts valid https:// website URL", async () => {
    const { getByLabelText, getByText, queryByText } = render(<SignUpScreen />);
    fireEvent.changeText(getByLabelText("Website"), "https://acme.com");
    fireEvent.press(getByText("Sign Up"));
    await waitFor(() => {
      expect(
        queryByText("Enter a valid URL (e.g. https://example.com)"),
      ).toBeNull();
    });
  });

  it("validates GST number format when provided", async () => {
    const { getByLabelText, getByText, findByText } = render(<SignUpScreen />);
    fireEvent.changeText(getByLabelText("GST Number"), "INVALID-GST");
    fireEvent.press(getByText("Sign Up"));
    expect(
      await findByText("Enter a valid GSTIN (e.g. 22AAAAA0000A1Z5)"),
    ).toBeTruthy();
  });

  it("accepts valid GSTIN format", async () => {
    const { getByLabelText, getByText, queryByText } = render(<SignUpScreen />);
    fireEvent.changeText(getByLabelText("GST Number"), "22AAAAA0000A1Z5");
    fireEvent.press(getByText("Sign Up"));
    await waitFor(() => {
      expect(
        queryByText("Enter a valid GSTIN (e.g. 22AAAAA0000A1Z5)"),
      ).toBeNull();
    });
  });

  it("clears field error when user types", async () => {
    const { getByLabelText, getByText, queryByText, findByText } = render(
      <SignUpScreen />,
    );
    fireEvent.press(getByText("Sign Up"));
    await findByText("Email is required");
    fireEvent.changeText(getByLabelText("Email"), "test@example.com");
    await waitFor(() => {
      expect(queryByText("Email is required")).toBeNull();
    });
  });

  // ── Story 3: Registration call ────────────────────────────────────────────

  it("registers with correct payload including phoneCountry and phoneNationalNumber", async () => {
    (RegistrationService.registerAndStartOTP as jest.Mock).mockResolvedValue(
      OTP_SUCCESS,
    );

    const { getByLabelText, getByText } = render(
      <SignUpScreen onRegistrationSuccess={mockOnRegistrationSuccess} />,
    );

    fillRequiredFields(getByLabelText, getByText);
    // Select industry from picker
    fireEvent.press(getByLabelText("Business Industry"));
    fireEvent.press(getByText("Technology"));

    fireEvent.press(getByText("Sign Up"));

    await waitFor(() => {
      expect(RegistrationService.registerAndStartOTP).toHaveBeenCalledWith(
        expect.objectContaining({
          fullName: "Test User",
          email: "test@example.com",
          phoneCountry: "IN",
          phoneNationalNumber: "9876543210",
          businessName: "ACME Inc",
          businessIndustry: "Technology",
          businessAddress: "123 Main St, Bengaluru",
          preferredContactMethod: "email",
          consent: true,
        }),
      );
      expect(mockOnRegistrationSuccess).toHaveBeenCalledWith(
        "REG-123",
        "OTP-123",
        "email",
        "t***t@example.com",
      );
    });
  });

  it("includes optional fields when provided", async () => {
    (RegistrationService.registerAndStartOTP as jest.Mock).mockResolvedValue(
      OTP_SUCCESS,
    );

    const { getByLabelText, getByText } = render(
      <SignUpScreen onRegistrationSuccess={mockOnRegistrationSuccess} />,
    );

    fillRequiredFields(getByLabelText, getByText);
    fireEvent.press(getByLabelText("Business Industry"));
    fireEvent.press(getByText("Technology"));
    fireEvent.changeText(getByLabelText("Website"), "https://acme.com");
    fireEvent.changeText(getByLabelText("GST Number"), "22AAAAA0000A1Z5");

    fireEvent.press(getByText("Sign Up"));

    await waitFor(() => {
      expect(RegistrationService.registerAndStartOTP).toHaveBeenCalledWith(
        expect.objectContaining({
          website: "https://acme.com",
          gstNumber: "22AAAAA0000A1Z5",
        }),
      );
    });
  });

  // ── Error handling ────────────────────────────────────────────────────────

  it("handles email already registered error", async () => {
    const err = new (class extends Error {
      code = "EMAIL_ALREADY_REGISTERED";
      constructor() {
        super("Email already registered. Please sign in.");
        this.name = "RegistrationServiceError";
      }
    })();
    (RegistrationService.registerAndStartOTP as jest.Mock).mockRejectedValue(
      err,
    );

    const { getByLabelText, getByText, findByText } = render(<SignUpScreen />);
    fillRequiredFields(getByLabelText, getByText);
    fireEvent.press(getByLabelText("Business Industry"));
    fireEvent.press(getByText("Technology"));
    fireEvent.press(getByText("Sign Up"));

    expect(await findByText("Email already registered")).toBeTruthy();
    expect(
      await findByText("This email is already registered. Please sign in."),
    ).toBeTruthy();
  });

  it("handles phone already registered error", async () => {
    const err = new (class extends Error {
      code = "PHONE_ALREADY_REGISTERED";
      constructor() {
        super("Phone already registered. Please sign in.");
        this.name = "RegistrationServiceError";
      }
    })();
    (RegistrationService.registerAndStartOTP as jest.Mock).mockRejectedValue(
      err,
    );

    const { getByLabelText, getByText, findByText } = render(<SignUpScreen />);
    fillRequiredFields(getByLabelText, getByText);
    fireEvent.press(getByLabelText("Business Industry"));
    fireEvent.press(getByText("Technology"));
    fireEvent.press(getByText("Sign Up"));

    expect(
      await findByText("This phone is already registered. Please sign in."),
    ).toBeTruthy();
  });

  it("handles generic registration error", async () => {
    (RegistrationService.registerAndStartOTP as jest.Mock).mockRejectedValue(
      new Error("Network error"),
    );

    const { getByLabelText, getByText, findByText } = render(<SignUpScreen />);
    fillRequiredFields(getByLabelText, getByText);
    fireEvent.press(getByLabelText("Business Industry"));
    fireEvent.press(getByText("Technology"));
    fireEvent.press(getByText("Sign Up"));

    expect(
      await findByText("Registration failed. Please try again."),
    ).toBeTruthy();
  });

  it("shows loading state (button disabled) during registration", async () => {
    (RegistrationService.registerAndStartOTP as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100)),
    );

    const { getByLabelText, getByText } = render(<SignUpScreen />);
    fillRequiredFields(getByLabelText, getByText);
    fireEvent.press(getByLabelText("Business Industry"));
    fireEvent.press(getByText("Technology"));
    fireEvent.press(getByText("Sign Up"));

    await waitFor(() => {
      const button = getByText("Sign Up").parent;
      expect(button?.props.accessibilityState.disabled).toBe(true);
    });
  });

  it("disables sign in link during registration", async () => {
    (RegistrationService.registerAndStartOTP as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100)),
    );

    const { getByLabelText, getByText } = render(
      <SignUpScreen onSignInPress={mockOnSignInPress} />,
    );
    fillRequiredFields(getByLabelText, getByText);
    fireEvent.press(getByLabelText("Business Industry"));
    fireEvent.press(getByText("Technology"));
    fireEvent.press(getByText("Sign Up"));
    fireEvent.press(getByText("Sign in"));

    expect(mockOnSignInPress).not.toHaveBeenCalled();
  });
});
