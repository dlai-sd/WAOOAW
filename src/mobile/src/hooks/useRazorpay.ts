/**
 * useRazorpay Hook
 * 
 * React hook for Razorpay payment processing in components
 * Provides loading states, error handling, and payment flow management
 */

import { useState, useCallback } from 'react';
import { Alert } from 'react-native';
import { razorpayService, PaymentParams, PaymentVerificationResponse } from '../services/payment/razorpay.service';
import { useAuthStore } from '../store/authStore';

interface UseRazorpayReturn {
  processPayment: (params: Omit<PaymentParams, 'userEmail' | 'userContact' | 'userName'>) => Promise<PaymentVerificationResponse | null>;
  isProcessing: boolean;
  error: string | null;
  clearError: () => void;
}

/**
 * Hook for Razorpay payment processing
 * 
 * @example
 * ```tsx
 * const { processPayment, isProcessing, error } = useRazorpay();
 * 
 * const handlePayment = async () => {
 *   const result = await processPayment({
 *     agentId: 'agent-123',
 *     planType: 'monthly',
 *     amount: 12000,
 *   });
 *   
 *   if (result) {
 *     navigation.navigate('HireConfirmation', { subscriptionId: result.subscription_id });
 *   }
 * };
 * ```
 */
export function useRazorpay(): UseRazorpayReturn {
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const user = useAuthStore((state) => state.user);

  const processPayment = useCallback(
    async (
      params: Omit<PaymentParams, 'userEmail' | 'userContact' | 'userName'>
    ): Promise<PaymentVerificationResponse | null> => {
      if (!user) {
        setError('User not authenticated');
        Alert.alert('Error', 'Please sign in to continue with payment');
        return null;
      }

      setIsProcessing(true);
      setError(null);

      try {
        // Add user details to payment params
        const paymentParams: PaymentParams = {
          ...params,
          userEmail: user.email || '',
          userContact: user.phone || '',
          userName: user.full_name || user.email || 'User',
        };

        // Process payment through service
        const result = await razorpayService.processPayment(paymentParams);

        setIsProcessing(false);
        
        // Show success alert
        Alert.alert(
          'Payment Successful!',
          `Your subscription has been activated. Payment ID: ${result.payment_id}`,
          [{ text: 'OK' }]
        );

        return result;
      } catch (err: any) {
        setIsProcessing(false);

        // Handle different error types
        let errorMessage = 'Payment failed. Please try again.';

        if (err.code === 0) {
          // User cancelled
          errorMessage = 'Payment cancelled';
          setError(errorMessage);
          return null;
        }

        if (err.code === 2) {
          // Network error
          errorMessage = 'Network error. Please check your connection.';
        } else if (err.description) {
          errorMessage = err.description;
        } else if (err.message) {
          errorMessage = err.message;
        }

        setError(errorMessage);

        // Show error alert
        Alert.alert(
          'Payment Failed',
          errorMessage,
          [
            {
              text: 'Retry',
              onPress: () => processPayment(params),
            },
            {
              text: 'Cancel',
              style: 'cancel',
            },
          ]
        );

        return null;
      }
    },
    [user]
  );

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    processPayment,
    isProcessing,
    error,
    clearError,
  };
}

/**
 * Hook for getting payment status
 */
export function usePaymentStatus(paymentId: string | null) {
  const [status, setStatus] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    if (!paymentId) return;

    setIsLoading(true);
    setError(null);

    try {
      const statusData = await razorpayService.getPaymentStatus(paymentId);
      setStatus(statusData);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch payment status');
    } finally {
      setIsLoading(false);
    }
  }, [paymentId]);

  return {
    status,
    isLoading,
    error,
    refetch: fetchStatus,
  };
}
