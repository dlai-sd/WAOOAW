import { gatewayRequestJson } from './gatewayApiClient'

export type CouponCheckoutInput = {
  couponCode: string
  agentId: string
  duration: string
  idempotencyKey?: string
}

export type CouponCheckoutResponse = {
  order_id: string
  payment_provider: 'coupon'
  amount: number
  currency: string
  coupon_code: string
  agent_id: string
  duration: string
  subscription_status: string
  trial_status: string
  subscription_id?: string | null
}

export async function couponCheckout(input: CouponCheckoutInput): Promise<CouponCheckoutResponse> {
  return gatewayRequestJson<CouponCheckoutResponse>('/cp/payments/coupon/checkout', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(input.idempotencyKey ? { 'Idempotency-Key': input.idempotencyKey } : {})
    },
    body: JSON.stringify({
      coupon_code: input.couponCode,
      agent_id: input.agentId,
      duration: input.duration
    })
  })
}
