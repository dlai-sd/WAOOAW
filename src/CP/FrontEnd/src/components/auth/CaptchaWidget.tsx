import { useEffect, useRef, useState } from 'react'

type CaptchaWidgetProps = {
  siteKey: string
  onToken: (token: string | null) => void
  onError?: (message: string) => void
}

declare global {
  interface Window {
    turnstile?: {
      render: (container: HTMLElement, options: Record<string, unknown>) => string
      reset?: (widgetId?: string) => void
      remove?: (widgetId: string) => void
    }
  }
}

let turnstileScriptPromise: Promise<void> | null = null

function loadTurnstileScript(): Promise<void> {
  if (typeof window !== 'undefined' && window.turnstile) {
    return Promise.resolve()
  }
  if (turnstileScriptPromise) return turnstileScriptPromise

  turnstileScriptPromise = new Promise<void>((resolve, reject) => {
    if (typeof window === 'undefined') {
      resolve()
      return
    }

    const existing = document.querySelector('script[data-waooaw-turnstile="1"]') as HTMLScriptElement | null
    if (existing) {
      existing.addEventListener('load', () => resolve())
      existing.addEventListener('error', () => reject(new Error('Failed to load Turnstile script')))
      // If it’s already loaded, resolve immediately.
      if ((window as any).turnstile) resolve()
      return
    }

    const script = document.createElement('script')
    script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit'
    script.async = true
    script.defer = true
    script.setAttribute('data-waooaw-turnstile', '1')
    script.addEventListener('load', () => resolve())
    script.addEventListener('error', () => reject(new Error('Failed to load Turnstile script')))
    document.head.appendChild(script)
  })

  return turnstileScriptPromise
}

function withTimeout<T>(promise: Promise<T>, timeoutMs: number): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const timer = window.setTimeout(() => reject(new Error('Timed out loading CAPTCHA')), timeoutMs)
    promise
      .then((value) => {
        window.clearTimeout(timer)
        resolve(value)
      })
      .catch((err) => {
        window.clearTimeout(timer)
        reject(err)
      })
  })
}

export default function CaptchaWidget({ siteKey, onToken, onError }: CaptchaWidgetProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const mountedRef = useRef(true)
  const widgetIdRef = useRef<string | null>(null)
  const onTokenRef = useRef(onToken)
  const onErrorRef = useRef(onError)
  const [status, setStatus] = useState<'idle' | 'loading' | 'ready' | 'failed'>('idle')

  useEffect(() => {
    onTokenRef.current = onToken
    onErrorRef.current = onError
  }, [onToken, onError])

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    async function setup() {
      if (!siteKey) {
        setStatus('failed')
        onErrorRef.current?.('CAPTCHA is not configured')
        onTokenRef.current(null)
        return
      }

      // If we already rendered a widget for this component instance, do not re-render
      // on parent rerenders (prevents flicker + token resets).
      if (widgetIdRef.current) {
        return
      }

      setStatus('loading')
      try {
        await withTimeout(loadTurnstileScript(), 8000)
        if (cancelled || !mountedRef.current) return

        if (!window.turnstile || !containerRef.current) {
          setStatus('failed')
          onErrorRef.current?.('CAPTCHA failed to load')
          onTokenRef.current(null)
          return
        }

        // Defensive: if something previously rendered into the container, clear it.
        containerRef.current.innerHTML = ''

        try {
          widgetIdRef.current = window.turnstile.render(containerRef.current, {
            sitekey: siteKey,
            callback: (token: string) => {
              if (!mountedRef.current) return
              setStatus('ready')
              onTokenRef.current(token)
            },
            'expired-callback': () => {
              if (!mountedRef.current) return
              onTokenRef.current(null)
            },
            'error-callback': () => {
              if (!mountedRef.current) return
              setStatus('failed')
              onTokenRef.current(null)
            }
          })
        } catch {
          setStatus('failed')
          onErrorRef.current?.('CAPTCHA failed to load')
          onTokenRef.current(null)
        }
      } catch {
        setStatus('failed')
        onErrorRef.current?.('CAPTCHA failed to load')
        onTokenRef.current(null)
      }
    }

    setup()

    return () => {
      cancelled = true
      if (widgetIdRef.current && window.turnstile?.remove) {
        try {
          window.turnstile.remove(widgetIdRef.current)
        } catch {
          // ignore
        }
      }
      widgetIdRef.current = null
    }
  }, [siteKey])

  return (
    <div>
      <div ref={containerRef} style={{ minHeight: 65 }} />
      {status === 'loading' ? (
        <div role="status" aria-live="polite" style={{ fontSize: '0.85rem' }}>
          Loading CAPTCHA…
        </div>
      ) : null}
      {status === 'failed' ? (
        <div role="status" aria-live="polite" style={{ fontSize: '0.85rem' }}>
          CAPTCHA failed to load. If you use an ad/tracker blocker, try disabling it for this page.
        </div>
      ) : null}
    </div>
  )
}
