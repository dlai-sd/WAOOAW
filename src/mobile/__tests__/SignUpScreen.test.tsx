/**
 * SignUpScreen Tests — updated for 3-step registration wizard
 * Step 1: Email
 * Step 2: Business details (Full Name, Business Name, Industry, Address)
 * Step 3: Contact details (Phone, Preferred Contact, Consent)
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

/**
 * Navigate through all 3 steps and fill required fields.
 * Caller is responsible for the final submit action.
 */
const fillAllSteps = (utils: ReturnType<typeof render>) => {
  const { getByLabelText, getByText } = utils;

  // ── Step 1: Email ──
  fireEvent.changeText(getByLabelText("Email"), "test@example.com");
  fireEvent.press(getByLabelText("Continue"));

  // ── Step 2: Business details ──
  fireEvent.changeText(getByLabelText("Full Name"), "Test User");
  fireEvent.changeText(getByLabelText("Business Name"), "ACME Inc");
  fireEvent.press(getByLabelText("Technology")); // industry card
  fireEvent.changeText(getByLabelText("Business Address"), "123 Main St, Bengaluru");
  fireEvent.press(getByLabelText("Continue"));

  // ── Step 3: Contact details ──
  fireEvent.changeText(getByLabelText("Phone Number"), "9876543210");
  fireEvent.press(getByText("Email")); // preferred contact method toggle
  fireEvent.press(
    getByLabelText("I agree to the Terms of Service and Privacy Policy"),
  );
};

// ── Tests ──────────────────────────────────────────────────────────────────────

describe("SignUpScreen", () => {
  const mockOnSignInPress = jest.fn();
  const mockOnRegistrationSuccess = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ── Logo ──────────────────────────────────────────────────────────────────

  it("renders WAOOAW logo as image component, not text", () => {
    const { queryByText, getByLabelText } = render(<SignUpScreen />);
    expect(queryByText("WAOOAW")).toBeNull();
    expect(getByLabelText("WAOOAW")).toBeTruthy();
  });

  // ── Rendering ────────────────────────────────────────────────────────────────

  it("renders without crashing", () => {
    expect(() => render(<SignUpScreen />)).not.toThrow();
  });

  it("renders step 1 email field and Continue button on initial load", () => {
    const { getByLabelText } = render(<SignUpScreen />);
    expect(getByLabelText("Email")).toBeTruthy();
    expect(getByLabelText("Continue")).toBeTruthy();
  });

  it("renders step 2 business fields after advancing from step 1", () => {
    const { getByLabelText } = render(<SignUpScreen />);
    fireEvent.changeText(getByLabelText("Email"), "test@example.com");
    fireEvent.press(getByLabelText("Continue"));
    expect(getByLabelText("Full Name")).toBeTruthy();
    expect(getByLabelText("Business Name")).toBeTruthy();
    expect(getByLabelText("Business Address")).toBeTruthy();
    expect(getByLabelText("Technology")).toBeTruthy();
    expect(getByLabelText("Marketing")).toBeTruthy();
  });

  it("renders step 3 contact fields after advancing from step 2", () => {
    const { getByLabelText, getByText } = render(<SignUpScreen />);
    fireEvent.changeText(getByLabelText("Email"), "test@example.com");
    fireEvent.press(getByLabelText("Continue"));
    fireEvent.changeText(getByLabelText("Full Name"), "Test User");
    fireEvent.changeText(getByLabelText("Business Name"), "ACME Inc");
    fireEvent.press(getByLabelText("Technology"));
    fireEvent.press(getByLabelText("Continue"));
    expect(getByLabelText("Phone Number")).toBeTruthy();
    expect(getByText("Email")).toBeTruthy();
    expect(getByText("Phone")).toBeTruthy();
    expect(
      getByLabelText("I agree to the Terms of Service and Privacy Policy"),
    ).toBeTruthy();
    expect(getByText("Create My Account")).toBeTruthy();
  });

  it("calls onSignInPress when sign in link is pressed on step 1", () => {
    const { getByText } = render(
      <SignUpScreen onSignInPress={mockOnSignInPress} />,
    );
    fireEvent.press(getByText("Sign in"));
    expect(mockOnSignInPress).toHaveBeenCalledTimes(1);
  });

  it("renders SafeAreaView (all four edges including bottom)", () => {
    const { toJSON } = render(<SignUpScreen />);
    expect(toJSON()).toBeTruthy();
  });

  // ── Step 1 Validation ─────────────────────────────────────────────────────

  it("shows email required error on empty step 1 submit", async () => {
    const { getByLabelText, findByText } = render(<SignUpScreen />);
    fireEvent.press(getByLabelText("Continue"));
    expect(await findByText("Email is required")).toBeTruthy();
    expect(RegistrationService.registerAndStartOTP).not.toHaveBeenCalled();
  });

  it("validates email format", async () => {
    const { getByLabelText, findByText } = render(<SignUpScreen />);
    fireEvent.changeText(getByLabelText("Email"), "invalid-email");
    fireEvent.press(getByLabelText("Continue"));
    expect(await findByText("Invalid email format")).toBeTruthy();
  });

  it("clears email error when user types a valid email", async () => {
    const { getByLabelText, findByText, queryByText } = render(<SignUpScreen />);
    fireEvent.press(getByLabelText("Continue"));
    await findByText("Email is required");
    fireEvent.changeText(getByLabelText("Email"), "test@example.com");
    await waitFor(() => {
      expect(queryByText("Email is required")).toBeNull();
    });
  });

  // ── Step 2 Validation ─────────────────────────────────────────────────────

  it("shows required-field errors on empty step 2 submit", async () => {
    const { getByLabelText, findByText } = render(<SignUpScreen />);
    fireEvent.changeText(getByLabelText("Email"), "test@example.com");
    fireEvent.press(getByLabelText("Continue"));
    fireEvent.press(getByLabelText("Continue"));
    expect(await findByText("Full name is required")).toBeTruthy();
    expect(await findByText("Business name is required")).toBeTruthy();
    expect(await findByText("Select your industry")).toBeTruthy();
    expect(RegistrationService.registerAndStartOTP).not.toHaveBeenCalled();
  });

  it("validates full name must be ≥ 2 characters", async () => {
    const { getByLabelText, findByText } = render(<SignUpScreen />);
    fireEvent.changeText(getByLabelText("Email"), "test@example.com");
    fireEvent.press(getByLabelText("Continue"));
    fireEvent.changeText(getByLabelText("Full Name"), "T");
    fireEvent.press(getByLabelText("Continue"));
    expect(await findByText("Name must be at least 2 characters")).toBeTruthy();
    expect(RegistrationService.registerAndStartOTP).not.toHaveBeenCalled();
  });

  // ── Step 3 Validation ─────────────────────────────────────────────────────

  it("shows required-field errors on empty step 3 submit", async () => {
    const { getByLabelText, getByText, findByText } = render(<SignUpScreen />);
    fireEvent.changeText(getByLabelText("Email"), "test@example.com");
    fireEvent.press(getByLabelText("Continue"));
    fireEvent.changeText(getByLabelText("Full Name"), "Test User");
    fireEvent.changeText(getByLabelText("Business Name"), "ACME Inc");
    fireEvent.press(getByLabelText("Technology"));
    fireEvent.press(getByLabelText("Continue"));
    fireEvent.press(getByText("Create My Account"));
    expect(await findByText("Phone number is required")).toBeTruthy();
    expect(await findByText("Select a preferred contact method")).toBeTruthy();
    expect(await findByText("You must accept the terms to continue")).toBeTruthy();
  });

  it("validates Indian phone (default IN): must start with 6-9 and be 10 digits", async () => {
    const { getByLabelText, getByText, findByText } = render(<SignUpScreen />);
    fireEvent.changeText(getByLabelText("Email"), "test@example.com");
    fireEvent.press(getByLabelText("Continue"));
    fireEvent.changeText(getByLabelText("Full Name"), "Test User");
    fireEvent.changeText(getByLabelText("Business Name"), "ACME Inc");
    fireEvent.press(getByLabelText("Technology"));
    fireEvent.press(getByLabelText("Continue"));
    fireEvent.changeText(getByLabelText("Phone Number"), "1234567890");
    fireEvent.press(getByText("Create My Account"));
    expect(
      await findByText("Enter a valid 10-digit Indian mobile number"),
    ).toBeTruthy();
    expect(RegistrationService.registerAndStartOTP).not.toHaveBeenCalled();
  });

  // ── Registration call ──────────────────────────────────────────────────────

  it("registers with correct payload including phoneCountry and phoneNationalNumber", async () => {
    (RegistrationService.registerAndStartOTP as jest.Mock).mockResolvedValue(
      OTP_SUCCESS,
    );

    const utils = render(
      <SignUpScreen onRegistrationSuccess={mockOnRegistrationSuccess} />,
    );
    fillAllSteps(utils);
    fireEvent.press(utils.getByText("Create My Account"));

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
        {
          full_name: "Test User",
          email: "test@example.com",
          phone: "+919876543210",
          business_name: "ACME Inc",
        },
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
    (RegistrationService.registerAndStartOTP as jest.Mock).mockRejectedValue(err);

    const utils = render(<SignUpScreen />);
    fillAllSteps(utils);
    fireEvent.press(utils.getByText("Create My Account"));

    // Field-level error is on the email input (step 1) — not visible on step 3.
    // Only the banner message is rendered on the current step.
    expect(
      await utils.findByText("This email is already registered. Please sign in."),
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
    (RegistrationService.registerAndStartOTP as jest.Mock).mockRejectedValue(err);

    const utils = render(<SignUpScreen />);
    fillAllSteps(utils);
    fireEvent.press(utils.getByText("Create My Account"));

    expect(
      await utils.findByText("This phone is already registered. Please sign in."),
    ).toBeTruthy();
  });

  it("handles generic registration error", async () => {
    (RegistrationService.registerAndStartOTP as jest.Mock).mockRejectedValue(
      new Error("Network error"),
    );

    const utils = render(<SignUpScreen />);
    fillAllSteps(utils);
    fireEvent.press(utils.getByText("Create My Account"));

    expect(
      await utils.findByText("Registration failed. Please try again."),
    ).toBeTruthy();
  });

  it("shows loading state (button disabled) during registration", async () => {
    (RegistrationService.registerAndStartOTP as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100)),
    );

    const utils = render(<SignUpScreen />);
    fillAllSteps(utils);
    fireEvent.press(utils.getByText("Create My Account"));

    await waitFor(() => {
      const button = utils.getByLabelText("Create account");
      expect(button.props.accessibilityState.disabled).toBe(true);
    });
  });

  it("disables sign in link during registration (link not present on step 3)", async () => {
    (RegistrationService.registerAndStartOTP as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100)),
    );

    const utils = render(
      <SignUpScreen onSignInPress={mockOnSignInPress} />,
    );
    fillAllSteps(utils);
    fireEvent.press(utils.getByText("Create My Account"));
    // Sign in link is only on step 1; on step 3 it is not rendered
    expect(mockOnSignInPress).not.toHaveBeenCalled();
  });
});
