/**
 * Razorpay Configuration
 * 
 * Test keys for development (replace with production keys when available)
 * See: https://razorpay.com/docs/payments/dashboard/account-settings/api-keys/
 */

export const razorpayConfig = {
  // Test/Sandbox keys (replace with production keys)
  keyId: typeof __DEV__ !== 'undefined' && __DEV__
    ? 'rzp_test_1234567890abcd' // Test key - replace with your test key
    : 'rzp_live_REPLACE_WITH_LIVE_KEY', // Production key
  
  keySecret: typeof __DEV__ !== 'undefined' && __DEV__
    ? 'test_secret_1234567890abcd' // Test secret - replace with your test secret
    : 'REPLACE_WITH_LIVE_SECRET', // Production secret

  // Payment options
  currency: 'INR',
  name: 'WAOOAW',
  description: 'AI Agent Subscription',
  image: 'https://waooaw.com/logo.png', // Replace with actual logo URL
  
  // Theme
  theme: {
    color: '#00f2fe', // Neon cyan from brand
  },

  // Prefill (will be populated dynamically)
  prefill: {
    email: '',
    contact: '',
    name: '',
  },

  // Notes (for tracking)
  notes: {
    platform: 'mobile',
    app_version: '1.0.0',
  },

  // Retry configuration
  retry: {
    enabled: true,
    max_count: 3,
  },

  // Timeout (in seconds)
  timeout: 300, // 5 minutes
};

/**
 * Test card details for sandbox mode
 * See: https://razorpay.com/docs/payments/payments/test-card-details/
 */
export const testCards = {
  success: {
    number: '4111 1111 1111 1111',
    cvv: '123',
    expiry: '12/25',
    name: 'Test User',
  },
  failure: {
    number: '4111 1111 1111 1112', // Will fail
    cvv: '123',
    expiry: '12/25',
    name: 'Test Failure',
  },
  insufficientFunds: {
    number: '5105 1051 0510 5100',
    cvv: '123',
    expiry: '12/25',
    name: 'Insufficient Funds',
  },
};

/**
 * Test UPI IDs for sandbox mode
 */
export const testUPIs = {
  success: 'success@razorpay',
  failure: 'failure@razorpay',
};

/**
 * Payment method configuration
 */
export const paymentMethods = {
  card: true,
  netbanking: true,
  upi: true,
  wallet: true,
  emi: false, // Disable EMI for now
  paylater: false,
};
