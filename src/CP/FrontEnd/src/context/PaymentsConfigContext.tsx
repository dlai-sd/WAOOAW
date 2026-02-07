import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import type { PaymentsConfig } from '../services/paymentsConfig.service'
import { getPaymentsConfig } from '../services/paymentsConfig.service'

type PaymentsConfigContextValue = {
  config: PaymentsConfig | null
  isLoading: boolean
  error: string | null
  refresh: () => Promise<void>
}

const PaymentsConfigContext = createContext<PaymentsConfigContextValue | undefined>(undefined)

export function PaymentsConfigProvider({ children }: { children: React.ReactNode }) {
  const [config, setConfig] = useState<PaymentsConfig | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const latest = await getPaymentsConfig()
      setConfig(latest)
    } catch (e: any) {
      setError(e instanceof Error ? e.message : String(e))
      setConfig(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const value = useMemo(
    () => ({ config, isLoading, error, refresh }),
    [config, isLoading, error, refresh]
  )

  return <PaymentsConfigContext.Provider value={value}>{children}</PaymentsConfigContext.Provider>
}

export function usePaymentsConfig(): PaymentsConfigContextValue {
  const ctx = useContext(PaymentsConfigContext)
  if (!ctx) {
    throw new Error('usePaymentsConfig must be used within a PaymentsConfigProvider')
  }
  return ctx
}
