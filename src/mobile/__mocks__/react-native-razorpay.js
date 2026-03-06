module.exports = {
  default: {
    open: jest.fn(() => Promise.resolve({ razorpay_payment_id: 'pay_test123', razorpay_order_id: 'order_test123', razorpay_signature: 'sig_test123' })),
  },
};
