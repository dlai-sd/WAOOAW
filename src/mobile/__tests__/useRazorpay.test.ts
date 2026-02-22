/**
 * useRazorpay Hook Tests
 * Tests for the Razorpay payment hook with mocked service
 */

import { renderHook, act, waitFor } from '@testing-library/react-native';
import { Alert } from 'react-native';
import { useRazorpay } from '../src/hooks/useRazorpay';
import { razorpayService } from '../src/services/payment/razorpay.service';
import { useAuthStore } from '../src/store/authStore';

// Mock Alert
jest.spyOn(Alert, 'alert');

// Mock razorpay service
jest.mock('../src/services/payment/razorpay.service', () => ({
  razorpayService: {
    processPayment: jest.fn(),
  },
}));

// Mock auth store
jest.mock('../src/store/authStore', () => ({
  useAuthStore: jest.fn(),
}));

describe('useRazorpay Hook', () => {
  const mockUser = {
    customer_id: 'user-123',
    email: 'test@example.com',
    phone: '+919876543210',
    full_name: 'Test User',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useAuthStore as unknown as jest.Mock).mockReturnValue(mockUser);
  });

  describe('processPayment', () => {
    it('should process payment successfully', async () => {
      const mockPaymentResult = {
        success: true,
        payment_id: 'pay_test123',
        subscription_id: 'sub_test123',
        message: 'Payment verified successfully',
      };

      (razorpayService.processPayment as jest.Mock).mockResolvedValue(mockPaymentResult);

      const { result } = renderHook(() => useRazorpay());

      expect(result.current.isProcessing).toBe(false);
      expect(result.current.error).toBeNull();

      let paymentResult;

      await act(async () => {
        paymentResult = await result.current.processPayment({
          agentId: 'agent-123',
          planType: 'monthly',
          amount: 12000,
        });
      });

      await waitFor(() => {
        expect(result.current.isProcessing).toBe(false);
      });

      expect(razorpayService.processPayment).toHaveBeenCalledWith({
        agentId: 'agent-123',
        planType: 'monthly',
        amount: 12000,
        userEmail: 'test@example.com',
        userContact: '+919876543210',
        userName: 'Test User',
      });

      expect(paymentResult).toEqual(mockPaymentResult);
      expect(result.current.error).toBeNull();
      expect(Alert.alert).toHaveBeenCalledWith(
        'Payment Successful!',
        expect.stringContaining('pay_test123'),
        [{ text: 'OK' }]
      );
    });

    it('should handle user not authenticated', async () => {
      (useAuthStore as unknown as jest.Mock).mockReturnValue(null);

      const { result } = renderHook(() => useRazorpay());

      let paymentResult;

      await act(async () => {
        paymentResult = await result.current.processPayment({
          agentId: 'agent-123',
          planType: 'monthly',
          amount: 12000,
        });
      });

      expect(paymentResult).toBeNull();
      expect(result.current.error).toBe('User not authenticated');
      expect(Alert.alert).toHaveBeenCalledWith('Error', 'Please sign in to continue with payment');
      expect(razorpayService.processPayment).not.toHaveBeenCalled();
    });

    it('should handle user cancellation', async () => {
      const mockCancellationError = {
        code: 0,
        description: 'Payment cancelled by user',
      };

      (razorpayService.processPayment as jest.Mock).mockRejectedValue(mockCancellationError);

      const { result } = renderHook(() => useRazorpay());

      let paymentResult;

      await act(async () => {
        paymentResult = await result.current.processPayment({
          agentId: 'agent-123',
          planType: 'trial',
          amount: 0,
        });
      });

      await waitFor(() => {
        expect(result.current.isProcessing).toBe(false);
      });

      expect(paymentResult).toBeNull();
      expect(result.current.error).toBe('Payment cancelled');
      expect(Alert.alert).not.toHaveBeenCalledWith(expect.stringContaining('Failed'));
    });

    it('should handle network error', async () => {
      const mockNetworkError = {
        code: 2,
        description: 'Network error',
      };

      (razorpayService.processPayment as jest.Mock).mockRejectedValue(mockNetworkError);

      const { result } = renderHook(() => useRazorpay());

      let paymentResult;

      await act(async () => {
        paymentResult = await result.current.processPayment({
          agentId: 'agent-123',
          planType: 'monthly',
          amount: 12000,
        });
      });

      await waitFor(() => {
        expect(result.current.isProcessing).toBe(false);
      });

      expect(paymentResult).toBeNull();
      expect(result.current.error).toBe('Network error. Please check your connection.');
      expect(Alert.alert).toHaveBeenCalledWith(
        'Payment Failed',
        'Network error. Please check your connection.',
        expect.arrayContaining([
          expect.objectContaining({ text: 'Retry' }),
          expect.objectContaining({ text: 'Cancel', style: 'cancel' }),
        ])
      );
    });

    it('should handle generic payment error', async () => {
      const mockError = {
        description: 'Insufficient funds',
      };

      (razorpayService.processPayment as jest.Mock).mockRejectedValue(mockError);

      const { result } = renderHook(() => useRazorpay());

      let paymentResult;

      await act(async () => {
        paymentResult = await result.current.processPayment({
          agentId: 'agent-123',
          planType: 'monthly',
          amount: 12000,
        });
      });

      await waitFor(() => {
        expect(result.current.isProcessing).toBe(false);
      });

      expect(paymentResult).toBeNull();
      expect(result.current.error).toBe('Insufficient funds');
      expect(Alert.alert).toHaveBeenCalledWith(
        'Payment Failed',
        'Insufficient funds',
        expect.any(Array)
      );
    });

    it('should handle error without description', async () => {
      const mockError = new Error('Unknown error');

      (razorpayService.processPayment as jest.Mock).mockRejectedValue(mockError);

      const { result } = renderHook(() => useRazorpay());

      let paymentResult;

      await act(async () => {
        paymentResult = await result.current.processPayment({
          agentId: 'agent-123',
          planType: 'monthly',
          amount: 12000,
        });
      });

      await waitFor(() => {
        expect(result.current.isProcessing).toBe(false);
      });

      expect(paymentResult).toBeNull();
      expect(result.current.error).toBe('Unknown error');
    });

    it('should set isProcessing during payment', async () => {
      let resolvePayment: (value: any) => void;
      const paymentPromise = new Promise((resolve) => {
        resolvePayment = resolve;
      });

      (razorpayService.processPayment as jest.Mock).mockImplementation(() => paymentPromise);

      const { result } = renderHook(() => useRazorpay());

      expect(result.current.isProcessing).toBe(false);

      act(() => {
        result.current.processPayment({
          agentId: 'agent-123',
          planType: 'monthly',
          amount: 12000,
        });
      });

      // Should be processing
      await waitFor(() => {
        expect(result.current.isProcessing).toBe(true);
      });

      // Resolve payment
      await act(async () => {
        resolvePayment!({
          success: true,
          payment_id: 'pay_test123',
          subscription_id: 'sub_test123',
        });
      });

      // Should be done processing
      await waitFor(() => {
        expect(result.current.isProcessing).toBe(false);
      });
    });
  });

  describe('clearError', () => {
    it('should clear error state', async () => {
      const mockError = {
        code: 2,
        description: 'Payment failed',
      };

      (razorpayService.processPayment as jest.Mock).mockRejectedValue(mockError);

      const { result } = renderHook(() => useRazorpay());

      // Trigger error
      await act(async () => {
        await result.current.processPayment({
          agentId: 'agent-123',
          planType: 'monthly',
          amount: 12000,
        });
      });

      await waitFor(() => {
        expect(result.current.error).toBe('Network error. Please check your connection.');
      });

      // Clear error
      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe('user details', () => {
    it('should use user email from auth store', async () => {
      const mockPaymentResult = {
        success: true,
        payment_id: 'pay_test123',
        subscription_id: 'sub_test123',
      };

      (razorpayService.processPayment as jest.Mock).mockResolvedValue(mockPaymentResult);

      const { result } = renderHook(() => useRazorpay());

      await act(async () => {
        await result.current.processPayment({
          agentId: 'agent-123',
          planType: 'monthly',
          amount: 12000,
        });
      });

      expect(razorpayService.processPayment).toHaveBeenCalledWith(
        expect.objectContaining({
          userEmail: 'test@example.com',
        })
      );
    });

    it('should handle missing user phone', async () => {
      (useAuthStore as unknown as jest.Mock).mockReturnValue({
        ...mockUser,
        phone: null,
      });

      const mockPaymentResult = {
        success: true,
        payment_id: 'pay_test123',
        subscription_id: 'sub_test123',
      };

      (razorpayService.processPayment as jest.Mock).mockResolvedValue(mockPaymentResult);

      const { result } = renderHook(() => useRazorpay());

      await act(async () => {
        await result.current.processPayment({
          agentId: 'agent-123',
          planType: 'monthly',
          amount: 12000,
        });
      });

      expect(razorpayService.processPayment).toHaveBeenCalledWith(
        expect.objectContaining({
          userContact: '',
        })
      );
    });

    it('should use email as fallback for userName', async () => {
      (useAuthStore as unknown as jest.Mock).mockReturnValue({
        ...mockUser,
        full_name: null,
      });

      const mockPaymentResult = {
        success: true,
        payment_id: 'pay_test123',
        subscription_id: 'sub_test123',
      };

      (razorpayService.processPayment as jest.Mock).mockResolvedValue(mockPaymentResult);

      const { result } = renderHook(() => useRazorpay());

      await act(async () => {
        await result.current.processPayment({
          agentId: 'agent-123',
          planType: 'monthly',
          amount: 12000,
        });
      });

      expect(razorpayService.processPayment).toHaveBeenCalledWith(
        expect.objectContaining({
          userName: 'test@example.com',
        })
      );
    });
  });
});
