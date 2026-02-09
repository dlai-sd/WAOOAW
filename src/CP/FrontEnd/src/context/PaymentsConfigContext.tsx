import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'

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
  const isMountedRef = useRef(true)

  useEffect(() => {
    return () => {
      isMountedRef.current = false
    }
  }, [])

  const [config, setConfig] = useState<PaymentsConfig | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    if (!isMountedRef.current) return
    setIsLoading(true)
    setError(null)

    try {
      const latest = await getPaymentsConfig()
      if (!isMountedRef.current) return
      setConfig(latest)
    } catch (e: any) {
      if (!isMountedRef.current) return
      setError(e instanceof Error ? e.message : String(e))
      setConfig(null)
    } finally {
      if (!isMountedRef.current) return
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
