import { gatewayRequestJson } from './gatewayApiClient'

export type RazorpayOrderCreateInput = {
  agentId: string
  duration: string
}

export type RazorpayOrderCreateResponse = {
  order_id: string
  subscription_id: string
  payment_provider: 'razorpay'
  currency: string
  amount: number
  razorpay_key_id: string
  razorpay_order_id: string
}

export async function createRazorpayOrder(
  input: RazorpayOrderCreateInput
): Promise<RazorpayOrderCreateResponse> {
  return gatewayRequestJson<RazorpayOrderCreateResponse>('/cp/payments/razorpay/order', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      agent_id: input.agentId,
      duration: input.duration
    })
  })
}

export type RazorpayConfirmInput = {
  orderId: string
  razorpayOrderId: string
  razorpayPaymentId: string
  razorpaySignature: string
}

export type RazorpayConfirmResponse = {
  order_id: string
  subscription_id: string
  payment_provider: 'razorpay'
  subscription_status: string
}

export async function confirmRazorpayPayment(input: RazorpayConfirmInput): Promise<RazorpayConfirmResponse> {
  return gatewayRequestJson<RazorpayConfirmResponse>('/cp/payments/razorpay/confirm', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      order_id: input.orderId,
      razorpay_order_id: input.razorpayOrderId,
      razorpay_payment_id: input.razorpayPaymentId,
      razorpay_signature: input.razorpaySignature
    })
  })
}
