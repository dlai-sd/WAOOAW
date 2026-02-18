/**
 * Razorpay Payment Service
 * 
 * Handles Razorpay SDK integration for agent subscription payments
 * Uses backend API for order creation and payment verification
 */

import RazorpayCheckout from 'react-native-razorpay';
import apiClient from '../../lib/apiClient';
import { razorpayConfig } from '../../config/razorpay.config';

/**
 * Razorpay order response from backend
 */
export interface RazorpayOrder {
  order_id: string;
  amount: number;
  currency: string;
  razorpay_key: string;
}

/**
 * Payment success response from Razorpay SDK
 */
export interface RazorpayPaymentSuccess {
  razorpay_payment_id: string;
  razorpay_order_id: string;
  razorpay_signature: string;
}

/**
 * Payment verification response from backend
 */
export interface PaymentVerificationResponse {
  success: boolean;
  payment_id: string;
  subscription_id: string;
  message: string;
}

/**
 * Payment initiation parameters
 */
export interface PaymentParams {
  agentId: string;
  planType: 'trial' | 'monthly' | 'annual';
  amount: number;
  userEmail: string;
  userContact: string;
  userName: string;
}

class RazorpayService {
  /**
   * Create Razorpay order via backend API
   */
  async createOrder(params: PaymentParams): Promise<RazorpayOrder> {
    try {
      const { data } = await apiClient.post('/v1/payments/create-order', {
        agent_id: params.agentId,
        plan_type: params.planType,
        amount: params.amount * 100, // Convert to paise
        currency: razorpayConfig.currency,
      });

      return {
        order_id: data.order_id,
        amount: data.amount,
        currency: data.currency,
        razorpay_key: data.razorpay_key || razorpayConfig.keyId,
      };
    } catch (error: any) {
      console.error('Failed to create Razorpay order:', error);
      throw new Error(
        error.response?.data?.message || 'Failed to create payment order'
      );
    }
  }

  /**
   * Open Razorpay checkout
   */
  async openCheckout(
    order: RazorpayOrder,
    params: PaymentParams
  ): Promise<RazorpayPaymentSuccess> {
    const options = {
      key: order.razorpay_key,
      amount: order.amount,
      currency: order.currency,
      name: razorpayConfig.name,
      description: `${razorpayConfig.description} - ${params.planType}`,
      image: razorpayConfig.image,
      order_id: order.order_id,
      prefill: {
        email: params.userEmail,
        contact: params.userContact,
        name: params.userName,
      },
      theme: razorpayConfig.theme,
      notes: {
        ...razorpayConfig.notes,
        agent_id: params.agentId,
        plan_type: params.planType,
      },
      retry: razorpayConfig.retry,
      timeout: razorpayConfig.timeout,
    };

    return new Promise((resolve, reject) => {
      RazorpayCheckout.open(options)
        .then((data: any) => {
          resolve({
            razorpay_payment_id: data.razorpay_payment_id,
            razorpay_order_id: data.razorpay_order_id,
            razorpay_signature: data.razorpay_signature,
          });
        })
        .catch((error: any) => {
          // User cancelled or payment failed
          console.log('Razorpay checkout error:', error);
          reject({
            code: error.code,
            description: error.description,
            reason: error.reason,
            step: error.step,
            source: error.source,
            metadata: error.metadata,
          });
        });
    });
  }

  /**
   * Verify payment with backend
   */
  async verifyPayment(
    paymentData: RazorpayPaymentSuccess,
    agentId: string,
    planType: string
  ): Promise<PaymentVerificationResponse> {
    try {
      const { data } = await apiClient.post('/v1/payments/verify', {
        razorpay_payment_id: paymentData.razorpay_payment_id,
        razorpay_order_id: paymentData.razorpay_order_id,
        razorpay_signature: paymentData.razorpay_signature,
        agent_id: agentId,
        plan_type: planType,
      });

      return {
        success: data.success,
        payment_id: data.payment_id,
        subscription_id: data.subscription_id,
        message: data.message || 'Payment verified successfully',
      };
    } catch (error: any) {
      console.error('Failed to verify payment:', error);
      throw new Error(
        error.response?.data?.message || 'Payment verification failed'
      );
    }
  }

  /**
   * Complete payment flow (create order -> checkout -> verify)
   */
  async processPayment(params: PaymentParams): Promise<PaymentVerificationResponse> {
    // Step 1: Create order
    const order = await this.createOrder(params);

    // Step 2: Open Razorpay checkout
    const paymentData = await this.openCheckout(order, params);

    // Step 3: Verify payment with backend
    const verification = await this.verifyPayment(
      paymentData,
      params.agentId,
      params.planType
    );

    return verification;
  }

  /**
   * Refund payment (admin only - for testing)
   */
  async refundPayment(paymentId: string, amount?: number): Promise<void> {
    try {
      await apiClient.post('/v1/payments/refund', {
        payment_id: paymentId,
        amount: amount ? amount * 100 : undefined, // Convert to paise if provided
      });
    } catch (error: any) {
      console.error('Failed to refund payment:', error);
      throw new Error(
        error.response?.data?.message || 'Payment refund failed'
      );
    }
  }

  /**
   * Get payment status
   */
  async getPaymentStatus(paymentId: string): Promise<any> {
    try {
      const { data } = await apiClient.get(`/v1/payments/${paymentId}/status`);
      return data;
    } catch (error: any) {
      console.error('Failed to get payment status:', error);
      throw new Error(
        error.response?.data?.message || 'Failed to fetch payment status'
      );
    }
  }
}

export const razorpayService = new RazorpayService();
