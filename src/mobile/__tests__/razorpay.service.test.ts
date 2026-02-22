/**
 * Razorpay Service Tests
 * Tests for Razorpay payment integration with mocked SDK
 */

import { razorpayService } from '../src/services/payment/razorpay.service';
import RazorpayCheckout from 'react-native-razorpay';
import apiClient from '../src/lib/apiClient';

// Mock the Razorpay SDK
jest.mock('react-native-razorpay', () => ({
  open: jest.fn(),
}));

// Mock API client
jest.mock('../src/lib/apiClient');

describe('Razorpay Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('createOrder', () => {
    it('should create payment order successfully', async () => {
      const mockOrderResponse = {
        data: {
          order_id: 'order_test123',
          amount: 1200000, // ₹12,000 in paise
          currency: 'INR',
          razorpay_key: 'rzp_test_123',
        },
      };

      (apiClient.post as jest.Mock).mockResolvedValue(mockOrderResponse);

      const params = {
        agentId: 'agent-123',
        planType: 'monthly' as const,
        amount: 12000,
        userEmail: 'test@example.com',
        userContact: '+919876543210',
        userName: 'Test User',
      };

      const result = await razorpayService.createOrder(params);

      expect(apiClient.post).toHaveBeenCalledWith('/v1/payments/create-order', {
        agent_id: 'agent-123',
        plan_type: 'monthly',
        amount: 1200000,
        currency: 'INR',
      });

      expect(result).toEqual({
        order_id: 'order_test123',
        amount: 1200000,
        currency: 'INR',
        razorpay_key: 'rzp_test_123',
      });
    });

    it('should handle order creation failure', async () => {
      const mockError = {
        response: {
          data: {
            message: 'Invalid agent ID',
          },
        },
      };

      (apiClient.post as jest.Mock).mockRejectedValue(mockError);

      const params = {
        agentId: 'invalid-agent',
        planType: 'monthly' as const,
        amount: 12000,
        userEmail: 'test@example.com',
        userContact: '+919876543210',
        userName: 'Test User',
      };

      await expect(razorpayService.createOrder(params)).rejects.toThrow('Invalid agent ID');
    });

    it('should handle network error during order creation', async () => {
      (apiClient.post as jest.Mock).mockRejectedValue(new Error('Network error'));

      const params = {
        agentId: 'agent-123',
        planType: 'trial' as const,
        amount: 0,
        userEmail: 'test@example.com',
        userContact: '+919876543210',
        userName: 'Test User',
      };

      await expect(razorpayService.createOrder(params)).rejects.toThrow('Failed to create payment order');
    });
  });

  describe('openCheckout', () => {
    it('should open Razorpay checkout successfully', async () => {
      const mockCheckoutResult = {
        razorpay_payment_id: 'pay_test123',
        razorpay_order_id: 'order_test123',
        razorpay_signature: 'signature_test123',
      };

      (RazorpayCheckout.open as jest.Mock).mockResolvedValue(mockCheckoutResult);

      const order = {
        order_id: 'order_test123',
        amount: 1200000,
        currency: 'INR',
        razorpay_key: 'rzp_test_123',
      };

      const params = {
        agentId: 'agent-123',
        planType: 'monthly' as const,
        amount: 12000,
        userEmail: 'test@example.com',
        userContact: '+919876543210',
        userName: 'Test User',
      };

      const result = await razorpayService.openCheckout(order, params);

      expect(RazorpayCheckout.open).toHaveBeenCalledWith(
        expect.objectContaining({
          key: 'rzp_test_123',
          amount: 1200000,
          currency: 'INR',
          order_id: 'order_test123',
          prefill: {
            email: 'test@example.com',
            contact: '+919876543210',
            name: 'Test User',
          },
        })
      );

      expect(result).toEqual(mockCheckoutResult);
    });

    it('should handle user cancellation', async () => {
      const mockError = {
        code: 0,
        description: 'Payment cancelled by user',
      };

      (RazorpayCheckout.open as jest.Mock).mockRejectedValue(mockError);

      const order = {
        order_id: 'order_test123',
        amount: 1200000,
        currency: 'INR',
        razorpay_key: 'rzp_test_123',
      };

      const params = {
        agentId: 'agent-123',
        planType: 'monthly' as const,
        amount: 12000,
        userEmail: 'test@example.com',
        userContact: '+919876543210',
        userName: 'Test User',
      };

      await expect(razorpayService.openCheckout(order, params)).rejects.toEqual(mockError);
    });

    it('should handle payment failure', async () => {
      const mockError = {
        code: 2,
        description: 'Payment failed due to insufficient funds',
      };

      (RazorpayCheckout.open as jest.Mock).mockRejectedValue(mockError);

      const order = {
        order_id: 'order_test123',
        amount: 1200000,
        currency: 'INR',
        razorpay_key: 'rzp_test_123',
      };

      const params = {
        agentId: 'agent-123',
        planType: 'monthly' as const,
        amount: 12000,
        userEmail: 'test@example.com',
        userContact: '+919876543210',
        userName: 'Test User',
      };

      await expect(razorpayService.openCheckout(order, params)).rejects.toEqual(mockError);
    });
  });

  describe('verifyPayment', () => {
    it('should verify payment successfully', async () => {
      const mockVerificationResponse = {
        data: {
          success: true,
          payment_id: 'pay_test123',
          subscription_id: 'sub_test123',
          message: 'Payment verified successfully',
        },
      };

      (apiClient.post as jest.Mock).mockResolvedValue(mockVerificationResponse);

      const paymentData = {
        razorpay_payment_id: 'pay_test123',
        razorpay_order_id: 'order_test123',
        razorpay_signature: 'signature_test123',
      };

      const result = await razorpayService.verifyPayment(paymentData, 'agent-123', 'monthly');

      expect(apiClient.post).toHaveBeenCalledWith('/v1/payments/verify', {
        razorpay_payment_id: 'pay_test123',
        razorpay_order_id: 'order_test123',
        razorpay_signature: 'signature_test123',
        agent_id: 'agent-123',
        plan_type: 'monthly',
      });

      expect(result).toEqual({
        success: true,
        payment_id: 'pay_test123',
        subscription_id: 'sub_test123',
        message: 'Payment verified successfully',
      });
    });

    it('should handle verification failure', async () => {
      const mockError = {
        response: {
          data: {
            message: 'Invalid signature',
          },
        },
      };

      (apiClient.post as jest.Mock).mockRejectedValue(mockError);

      const paymentData = {
        razorpay_payment_id: 'pay_test123',
        razorpay_order_id: 'order_test123',
        razorpay_signature: 'invalid_signature',
      };

      await expect(razorpayService.verifyPayment(paymentData, 'agent-123', 'monthly')).rejects.toThrow('Invalid signature');
    });
  });

  describe('processPayment', () => {
    it('should complete full payment flow successfully', async () => {
      // Mock order creation
      const mockOrderResponse = {
        data: {
          order_id: 'order_test123',
          amount: 1200000,
          currency: 'INR',
          razorpay_key: 'rzp_test_123',
        },
      };

      // Mock checkout success
      const mockCheckoutResult = {
        razorpay_payment_id: 'pay_test123',
        razorpay_order_id: 'order_test123',
        razorpay_signature: 'signature_test123',
      };

      // Mock verification success
      const mockVerificationResponse = {
        data: {
          success: true,
          payment_id: 'pay_test123',
          subscription_id: 'sub_test123',
          message: 'Payment verified successfully',
        },
      };

      (apiClient.post as jest.Mock)
        .mockResolvedValueOnce(mockOrderResponse) // createOrder
        .mockResolvedValueOnce(mockVerificationResponse); // verifyPayment

      (RazorpayCheckout.open as jest.Mock).mockResolvedValue(mockCheckoutResult);

      const params = {
        agentId: 'agent-123',
        planType: 'monthly' as const,
        amount: 12000,
        userEmail: 'test@example.com',
        userContact: '+919876543210',
        userName: 'Test User',
      };

      const result = await razorpayService.processPayment(params);

      expect(result).toEqual({
        success: true,
        payment_id: 'pay_test123',
        subscription_id: 'sub_test123',
        message: 'Payment verified successfully',
      });

      // Verify all steps were called
      expect(apiClient.post).toHaveBeenCalledTimes(2);
      expect(RazorpayCheckout.open).toHaveBeenCalledTimes(1);
    });

    it('should handle user cancellation in full flow', async () => {
      // Mock order creation
      const mockOrderResponse = {
        data: {
          order_id: 'order_test123',
          amount: 1200000,
          currency: 'INR',
          razorpay_key: 'rzp_test_123',
        },
      };

      (apiClient.post as jest.Mock).mockResolvedValue(mockOrderResponse);

      // Mock user cancellation
      const mockCancellationError = {
        code: 0,
        description: 'Payment cancelled by user',
      };

      (RazorpayCheckout.open as jest.Mock).mockRejectedValue(mockCancellationError);

      const params = {
        agentId: 'agent-123',
        planType: 'trial' as const,
        amount: 0,
        userEmail: 'test@example.com',
        userContact: '+919876543210',
        userName: 'Test User',
      };

      await expect(razorpayService.processPayment(params)).rejects.toEqual(mockCancellationError);

      // Verification should not be called
      expect(apiClient.post).toHaveBeenCalledTimes(1);
    });

    it('should handle payment failure in full flow', async () => {
      // Mock order creation
      const mockOrderResponse = {
        data: {
          order_id: 'order_test123',
          amount: 1200000,
          currency: 'INR',
          razorpay_key: 'rzp_test_123',
        },
      };

      (apiClient.post as jest.Mock).mockResolvedValue(mockOrderResponse);

      // Mock payment failure
      const mockPaymentError = {
        code: 2,
        description: 'Payment failed',
      };

      (RazorpayCheckout.open as jest.Mock).mockRejectedValue(mockPaymentError);

      const params = {
        agentId: 'agent-123',
        planType: 'monthly' as const,
        amount: 12000,
        userEmail: 'test@example.com',
        userContact: '+919876543210',
        userName: 'Test User',
      };

      await expect(razorpayService.processPayment(params)).rejects.toEqual(mockPaymentError);
    });
  });
});
