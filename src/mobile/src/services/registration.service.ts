/**
 * Registration Service
 * Handles customer registration flow:
 * 1. POST /auth/register    - Create registration (Plant Gateway — AUTH-MOBILE-REG-1)
 * 2. POST /auth/otp/start   - Start OTP verification (Plant Gateway — AUTH-MOBILE-OTP-1)
 * 3. POST /auth/otp/verify  - Verify OTP and get tokens (Plant Gateway — AUTH-MOBILE-OTP-1)
 *
 * All three steps call Plant Gateway directly (apiClient → EXPO_PUBLIC_API_URL = plant.*.waooaw.com).
 */

import apiClient from "../lib/apiClient";
import { TokenManagerService, TokenResponse } from "./tokenManager.service";
import secureStorage from "../lib/secureStorage";

/**
 * Registration Request (CP parity — matches web AuthPanel)
 */
export interface RegistrationData {
  fullName: string;
  email: string;
  /** ISO 3166-1 alpha-2 country code, e.g. 'IN', 'US' */
  phoneCountry: string;
  /** National number without country code, e.g. '9876543210' */
  phoneNationalNumber: string;
  businessName: string;
  businessIndustry: string;
  businessAddress: string;
  website?: string;
  gstNumber?: string;
  preferredContactMethod: "email" | "phone";
  consent: boolean;
}

/**
 * Registration Response
 */
export interface RegistrationResponse {
  registration_id: string;
  email: string;
  phone: string;
}

/**
 * OTP Start Response
 */
export interface OTPStartResponse {
  otp_id: string;
  channel: "email" | "phone";
  destination_masked: string;
  expires_in_seconds: number;
  otp_code?: string | null; // Only in development
}

/**
 * Registration Service Error
 */
export class RegistrationServiceError extends Error {
  constructor(
    message: string,
    public code: string,
    public originalError?: Error,
  ) {
    super(message);
    this.name = "RegistrationServiceError";
  }
}

/**
 * Registration Error Codes
 */
export const RegistrationErrorCode = {
  INVALID_INPUT: "INVALID_INPUT",
  EMAIL_ALREADY_REGISTERED: "EMAIL_ALREADY_REGISTERED",
  PHONE_ALREADY_REGISTERED: "PHONE_ALREADY_REGISTERED",
  REGISTRATION_FAILED: "REGISTRATION_FAILED",
  OTP_START_FAILED: "OTP_START_FAILED",
  OTP_VERIFY_FAILED: "OTP_VERIFY_FAILED",
  INVALID_OTP_CODE: "INVALID_OTP_CODE",
  OTP_EXPIRED: "OTP_EXPIRED",
  TOO_MANY_ATTEMPTS: "TOO_MANY_ATTEMPTS",
} as const;

/**
 * Registration Service
 * Static methods for stateless operation
 */
export class RegistrationService {
  /**
   * Register new customer
   *
   * Step 1 of registration flow.
   * Creates a registration_id for OTP verification.
   *
   * @param data - Registration data
   * @returns Registration response with registration_id
   * @throws RegistrationServiceError
   */
  static async register(data: RegistrationData): Promise<RegistrationResponse> {
    try {
      // Validate required inputs
      if (!data.fullName || !data.email || !data.phoneNationalNumber) {
        throw new RegistrationServiceError(
          "Full name, email, and phone are required",
          RegistrationErrorCode.INVALID_INPUT,
        );
      }

      // Build E.164 phone number from country + national number
      const DIAL_CODES: Record<string, string> = {
        IN: "+91",
        US: "+1",
        GB: "+44",
        AE: "+971",
        SG: "+65",
        AU: "+61",
        CA: "+1",
      };
      const dialCode = DIAL_CODES[data.phoneCountry] ?? "+91";
      const phone = `${dialCode}${data.phoneNationalNumber.trim()}`;

      // Prepare payload for CP backend
      const payload: Record<string, unknown> = {
        fullName: data.fullName.trim(),
        businessName: data.businessName.trim(),
        businessIndustry: data.businessIndustry.trim(),
        businessAddress: data.businessAddress.trim(),
        email: data.email.trim().toLowerCase(),
        phone,
        preferredContactMethod: data.preferredContactMethod,
        consent: data.consent,
      };

      if (data.website?.trim()) payload.website = data.website.trim();
      if (data.gstNumber?.trim())
        payload.gst_number = data.gstNumber.trim().toUpperCase();

      // Call Plant Gateway registration endpoint (AUTH-MOBILE-REG-1)
      const response = await apiClient.post<RegistrationResponse>(
        "/auth/register",
        payload,
      );

      return response.data;
    } catch (error: any) {
      // Handle specific error cases
      if (error.response?.status === 409) {
        const detail = error.response?.data?.detail || "";
        if (detail.toLowerCase().includes("email")) {
          throw new RegistrationServiceError(
            "Email already registered. Please sign in.",
            RegistrationErrorCode.EMAIL_ALREADY_REGISTERED,
            error,
          );
        }
        if (detail.toLowerCase().includes("phone")) {
          throw new RegistrationServiceError(
            "Phone already registered. Please sign in.",
            RegistrationErrorCode.PHONE_ALREADY_REGISTERED,
            error,
          );
        }
      }

      throw new RegistrationServiceError(
        error.response?.data?.detail ||
          "Registration failed. Please try again.",
        RegistrationErrorCode.REGISTRATION_FAILED,
        error,
      );
    }
  }

  /**
   * Start OTP verification
   *
   * Step 2 of registration flow.
   * Sends OTP to user's email or phone.
   *
   * @param registrationId - Registration ID from register()
   * @param channel - 'email' or 'phone' (optional, defaults to preferred method)
   * @returns OTP start response with otp_id
   * @throws RegistrationServiceError
   */
  static async startOTP(
    registrationId: string,
    channel?: "email" | "phone",
  ): Promise<OTPStartResponse> {
    try {
      if (!registrationId) {
        throw new RegistrationServiceError(
          "Registration ID is required",
          RegistrationErrorCode.INVALID_INPUT,
        );
      }

      const payload: { registration_id: string; channel?: "email" | "phone" } =
        {
          registration_id: registrationId,
        };

      if (channel) {
        payload.channel = channel;
      }

      const response = await apiClient.post<OTPStartResponse>(
        "/auth/otp/start",
        payload,
      );

      return response.data;
    } catch (error: any) {
      if (error.response?.status === 429) {
        throw new RegistrationServiceError(
          "Too many OTP requests. Please wait and try again.",
          RegistrationErrorCode.TOO_MANY_ATTEMPTS,
          error,
        );
      }

      throw new RegistrationServiceError(
        error.response?.data?.detail || "Failed to send OTP. Please try again.",
        RegistrationErrorCode.OTP_START_FAILED,
        error,
      );
    }
  }

  /**
   * Verify OTP and complete registration
   *
   * Step 3 of registration flow.
   * Verifies OTP code and returns JWT tokens.
   * Automatically saves tokens to secure storage.
   *
   * @param otpId - OTP ID from start OTP()
   * @param code - 6-digit OTP code
   * @returns Token response (access_token, refresh_token)
   * @throws RegistrationServiceError
   */
  static async verifyOTP(otpId: string, code: string): Promise<TokenResponse> {
    try {
      if (!otpId || !code) {
        throw new RegistrationServiceError(
          "OTP ID and code are required",
          RegistrationErrorCode.INVALID_INPUT,
        );
      }

      // Validate OTP code format (6 digits)
      if (!/^\d{6}$/.test(code)) {
        throw new RegistrationServiceError(
          "OTP code must be 6 digits",
          RegistrationErrorCode.INVALID_OTP_CODE,
        );
      }

      const payload = {
        otp_id: otpId,
        code: code.trim(),
      };

      const response = await apiClient.post<TokenResponse>(
        "/auth/otp/verify",
        payload,
      );

      // Save tokens to secure storage
      await TokenManagerService.saveTokens(response.data);

      return response.data;
    } catch (error: any) {
      if (error.response?.status === 400) {
        const detail = error.response?.data?.detail || "";
        if (detail.toLowerCase().includes("expired")) {
          throw new RegistrationServiceError(
            "OTP has expired. Please request a new one.",
            RegistrationErrorCode.OTP_EXPIRED,
            error,
          );
        }
        if (
          detail.toLowerCase().includes("invalid") ||
          detail.toLowerCase().includes("incorrect")
        ) {
          throw new RegistrationServiceError(
            "Invalid OTP code. Please try again.",
            RegistrationErrorCode.INVALID_OTP_CODE,
            error,
          );
        }
      }

      throw new RegistrationServiceError(
        error.response?.data?.detail ||
          "OTP verification failed. Please try again.",
        RegistrationErrorCode.OTP_VERIFY_FAILED,
        error,
      );
    }
  }

  /**
   * Complete registration flow
   *
   * Convenience method that combines register + startOTP.
   * Use this when you want to register and immediately send OTP.
   *
   * @param data - Registration data
   * @param channel - OTP delivery channel (optional)
   * @returns Object with registration_id and OTP info
   * @throws RegistrationServiceError
   */
  static async registerAndStartOTP(
    data: RegistrationData,
    channel?: "email" | "phone",
  ): Promise<{
    registration: RegistrationResponse;
    otp: OTPStartResponse;
  }> {
    const registration = await this.register(data);
    const otp = await this.startOTP(registration.registration_id, channel);
    return { registration, otp };
  }
}

export default RegistrationService;
