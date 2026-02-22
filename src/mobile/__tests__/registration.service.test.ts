/**
 * Registration Service Tests
 */

import RegistrationService, {
  RegistrationServiceError,
  RegistrationErrorCode,
} from '../src/services/registration.service';
import apiClient from '../src/lib/apiClient';
import { TokenManagerService } from '../src/services/tokenManager.service';

// Mock dependencies
jest.mock('../src/lib/apiClient');
jest.mock('../src/services/tokenManager.service');

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('RegistrationService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('register', () => {
    it('should successfully register a user', async () => {
      const mockResponse = {
        data: {
          registration_id: 'REG-123',
          email: 'test@example.com',
          phone: '+919876543210',
        },
      };

      mockApiClient.post.mockResolvedValue(mockResponse);

      const registrationData = {
        fullName: 'Test User',
        email: 'test@example.com',
        phone: '+919876543210',
      };

      const result = await RegistrationService.register(registrationData);

      expect(mockApiClient.post).toHaveBeenCalledWith('/cp/auth/register', {
        fullName: 'Test User',
        businessName: 'Test User',
        businessIndustry: 'general',
        businessAddress: 'Mobile Registration',
        email: 'test@example.com',
        phone: '+919876543210',
        preferredContactMethod: 'email',
        consent: true,
      });

      expect(result).toEqual({
        registration_id: 'REG-123',
        email: 'test@example.com',
        phone: '+919876543210',
      });
    });

    it('should use provided business name and industry', async () => {
      const mockResponse = {
        data: {
          registration_id: 'REG-123',
          email: 'test@example.com',
          phone: '+919876543210',
        },
      };

      mockApiClient.post.mockResolvedValue(mockResponse);

      const registrationData = {
        fullName: 'Test User',
        email: 'test@example.com',
        phone: '+919876543210',
        businessName: 'ACME Inc',
        businessIndustry: 'marketing',
        businessAddress: 'Bengaluru',
        preferredContactMethod: 'phone' as const,
      };

      await RegistrationService.register(registrationData);

      expect(mockApiClient.post).toHaveBeenCalledWith('/cp/auth/register', {
        fullName: 'Test User',
        businessName: 'ACME Inc',
        businessIndustry: 'marketing',
        businessAddress: 'Bengaluru',
        email: 'test@example.com',
        phone: '+919876543210',
        preferredContactMethod: 'phone',
        consent: true,
      });
    });

    it('should throw error for missing required fields', async () => {
      await expect(
        RegistrationService.register({
          fullName: '',
          email: 'test@example.com',
          phone: '+919876543210',
        })
      ).rejects.toThrow(RegistrationServiceError);

      await expect(
        RegistrationService.register({
          fullName: 'Test User',
          email: '',
          phone: '+919876543210',
        })
      ).rejects.toThrow(RegistrationServiceError);

      await expect(
        RegistrationService.register({
          fullName: 'Test User',
          email: 'test@example.com',
          phone: '',
        })
      ).rejects.toThrow(RegistrationServiceError);
    });

    it('should handle email already registered error', async () => {
      mockApiClient.post.mockRejectedValue({
        response: {
          status: 409,
          data: { detail: 'Email already registered. Please log in.' },
        },
      });

      await expect(
        RegistrationService.register({
          fullName: 'Test User',
          email: 'test@example.com',
          phone: '+919876543210',
        })
      ).rejects.toThrow(RegistrationServiceError);

      try {
        await RegistrationService.register({
          fullName: 'Test User',
          email: 'test@example.com',
          phone: '+919876543210',
        });
      } catch (error) {
        expect(error).toBeInstanceOf(RegistrationServiceError);
        expect((error as RegistrationServiceError).code).toBe(
          RegistrationErrorCode.EMAIL_ALREADY_REGISTERED
        );
      }
    });

    it('should handle phone already registered error', async () => {
      mockApiClient.post.mockRejectedValue({
        response: {
          status: 409,
          data: { detail: 'Phone already registered. Please log in.' },
        },
      });

      try {
        await RegistrationService.register({
          fullName: 'Test User',
          email: 'test@example.com',
          phone: '+919876543210',
        });
      } catch (error) {
        expect(error).toBeInstanceOf(RegistrationServiceError);
        expect((error as RegistrationServiceError).code).toBe(
          RegistrationErrorCode.PHONE_ALREADY_REGISTERED
        );
      }
    });

    it('should handle generic registration error', async () => {
      mockApiClient.post.mockRejectedValue({
        response: {
          status: 400,
          data: { detail: 'Invalid input' },
        },
      });

      try {
        await RegistrationService.register({
          fullName: 'Test User',
          email: 'test@example.com',
          phone: '+919876543210',
        });
      } catch (error) {
        expect(error).toBeInstanceOf(RegistrationServiceError);
        expect((error as RegistrationServiceError).code).toBe(
          RegistrationErrorCode.REGISTRATION_FAILED
        );
      }
    });
  });

  describe('startOTP', () => {
    it('should successfully start OTP', async () => {
      const mockResponse = {
        data: {
          otp_id: 'OTP-123',
          channel: 'email',
          destination_masked: 't***t@example.com',
          expires_in_seconds: 300,
        },
      };

      mockApiClient.post.mockResolvedValue(mockResponse);

      const result = await RegistrationService.startOTP('REG-123');

      expect(mockApiClient.post).toHaveBeenCalledWith('/cp/auth/otp/start', {
        registration_id: 'REG-123',
      });

      expect(result).toEqual({
        otp_id: 'OTP-123',
        channel: 'email',
        destination_masked: 't***t@example.com',
        expires_in_seconds: 300,
      });
    });

    it('should include channel when specified', async () => {
      const mockResponse = {
        data: {
          otp_id: 'OTP-123',
          channel: 'phone',
          destination_masked: '+91****3210',
          expires_in_seconds: 300,
        },
      };

      mockApiClient.post.mockResolvedValue(mockResponse);

      await RegistrationService.startOTP('REG-123', 'phone');

      expect(mockApiClient.post).toHaveBeenCalledWith('/cp/auth/otp/start', {
        registration_id: 'REG-123',
        channel: 'phone',
      });
    });

    it('should throw error for missing registration ID', async () => {
      await expect(RegistrationService.startOTP('')).rejects.toThrow(
        RegistrationServiceError
      );
    });

    it('should handle too many attempts error', async () => {
      mockApiClient.post.mockRejectedValue({
        response: {
          status: 429,
          data: { detail: 'Too many OTP requests' },
        },
      });

      try {
        await RegistrationService.startOTP('REG-123');
      } catch (error) {
        expect(error).toBeInstanceOf(RegistrationServiceError);
        expect((error as RegistrationServiceError).code).toBe(
          RegistrationErrorCode.TOO_MANY_ATTEMPTS
        );
      }
    });
  });

  describe('verifyOTP', () => {
    it('should successfully verify OTP and save tokens', async () => {
      const mockResponse = {
        data: {
          access_token: 'access_token_123',
          refresh_token: 'refresh_token_123',
          token_type: 'bearer',
          expires_in: 900,
        },
      };

      mockApiClient.post.mockResolvedValue(mockResponse);
      (TokenManagerService.saveTokens as jest.Mock).mockResolvedValue(undefined);

      const result = await RegistrationService.verifyOTP('OTP-123', '123456');

      expect(mockApiClient.post).toHaveBeenCalledWith('/cp/auth/otp/verify', {
        otp_id: 'OTP-123',
        code: '123456',
      });

      expect(TokenManagerService.saveTokens).toHaveBeenCalledWith({
        access_token: 'access_token_123',
        refresh_token: 'refresh_token_123',
        token_type: 'bearer',
        expires_in: 900,
      });

      expect(result).toEqual({
        access_token: 'access_token_123',
        refresh_token: 'refresh_token_123',
        token_type: 'bearer',
        expires_in: 900,
      });
    });

    it('should throw error for invalid OTP format', async () => {
      await expect(
        RegistrationService.verifyOTP('OTP-123', '12345')
      ).rejects.toThrow(RegistrationServiceError);

      await expect(
        RegistrationService.verifyOTP('OTP-123', '1234567')
      ).rejects.toThrow(RegistrationServiceError);

      await expect(
        RegistrationService.verifyOTP('OTP-123', 'abcdef')
      ).rejects.toThrow(RegistrationServiceError);
    });

    it('should handle invalid OTP code error', async () => {
      mockApiClient.post.mockRejectedValue({
        response: {
          status: 400,
          data: { detail: 'Invalid OTP code' },
        },
      });

      try {
        await RegistrationService.verifyOTP('OTP-123', '123456');
      } catch (error) {
        expect(error).toBeInstanceOf(RegistrationServiceError);
        expect((error as RegistrationServiceError).code).toBe(
          RegistrationErrorCode.INVALID_OTP_CODE
        );
      }
    });

    it('should handle expired OTP error', async () => {
      mockApiClient.post.mockRejectedValue({
        response: {
          status: 400,
          data: { detail: 'OTP has expired' },
        },
      });

      try {
        await RegistrationService.verifyOTP('OTP-123', '123456');
      } catch (error) {
        expect(error).toBeInstanceOf(RegistrationServiceError);
        expect((error as RegistrationServiceError).code).toBe(
          RegistrationErrorCode.OTP_EXPIRED
        );
      }
    });
  });

  describe('registerAndStartOTP', () => {
    it('should complete registration and start OTP flow', async () => {
      const mockRegResponse = {
        data: {
          registration_id: 'REG-123',
          email: 'test@example.com',
          phone: '+919876543210',
        },
      };

      const mockOTPResponse = {
        data: {
          otp_id: 'OTP-123',
          channel: 'email',
          destination_masked: 't***t@example.com',
          expires_in_seconds: 300,
        },
      };

      mockApiClient.post
        .mockResolvedValueOnce(mockRegResponse)
        .mockResolvedValueOnce(mockOTPResponse);

      const result = await RegistrationService.registerAndStartOTP({
        fullName: 'Test User',
        email: 'test@example.com',
        phone: '+919876543210',
      });

      expect(mockApiClient.post).toHaveBeenCalledTimes(2);
      expect(result).toEqual({
        registration: mockRegResponse.data,
        otp: mockOTPResponse.data,
      });
    });

    it('should pass channel to OTP start', async () => {
      const mockRegResponse = {
        data: {
          registration_id: 'REG-123',
          email: 'test@example.com',
          phone: '+919876543210',
        },
      };

      const mockOTPResponse = {
        data: {
          otp_id: 'OTP-123',
          channel: 'phone',
          destination_masked: '+91****3210',
          expires_in_seconds: 300,
        },
      };

      mockApiClient.post
        .mockResolvedValueOnce(mockRegResponse)
        .mockResolvedValueOnce(mockOTPResponse);

      await RegistrationService.registerAndStartOTP(
        {
          fullName: 'Test User',
          email: 'test@example.com',
          phone: '+919876543210',
        },
        'phone'
      );

      expect(mockApiClient.post).toHaveBeenLastCalledWith('/cp/auth/otp/start', {
        registration_id: 'REG-123',
        channel: 'phone',
      });
    });
  });
});
