import { describe, it, expect, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { PaymentsConfigProvider, usePaymentsConfig } from '../context/PaymentsConfigContext'
import type { ReactNode } from 'react'

vi.mock('../services/paymentsConfig.service', () => ({
  getPaymentsConfig: vi.fn().mockResolvedValue({ mode: 'coupon', coupon_code: 'WAOOAW100', coupon_unlimited: true })
}))

describe('PaymentsConfigContext', () => {
  const wrapper = ({ children }: { children: ReactNode }) => (
    <PaymentsConfigProvider>{children}</PaymentsConfigProvider>
  )

  it('loads payments config on mount', async () => {
    const { result } = renderHook(() => usePaymentsConfig(), { wrapper })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.error).toBeNull()
    expect(result.current.config?.mode).toBe('coupon')
    expect(result.current.config?.coupon_code).toBe('WAOOAW100')
  })
})
