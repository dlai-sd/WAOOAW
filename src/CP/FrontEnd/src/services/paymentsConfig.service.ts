import { gatewayRequestJson } from './gatewayApiClient'

export type PaymentsMode = 'razorpay' | 'coupon'

export type PaymentsConfig = {
  mode: PaymentsMode
  coupon_code?: string | null
  coupon_unlimited?: boolean | null
}

export async function getPaymentsConfig(): Promise<PaymentsConfig> {
  return gatewayRequestJson<PaymentsConfig>('/cp/payments/config')
}
