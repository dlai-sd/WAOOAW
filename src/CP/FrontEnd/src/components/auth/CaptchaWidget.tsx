import { useEffect, useRef } from 'react'

type CaptchaWidgetProps = {
  siteKey: string
  onToken: (token: string | null) => void
}

declare global {
  interface Window {
    turnstile?: {
      render: (container: HTMLElement, options: Record<string, unknown>) => string
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

export default function CaptchaWidget({ siteKey, onToken }: CaptchaWidgetProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    async function setup() {
      try {
        await loadTurnstileScript()
        if (cancelled || !mountedRef.current) return

        if (!window.turnstile || !containerRef.current) {
          onToken(null)
          return
        }

        window.turnstile.render(containerRef.current, {
          sitekey: siteKey,
          callback: (token: string) => {
            if (!mountedRef.current) return
            onToken(token)
          },
          'expired-callback': () => {
            if (!mountedRef.current) return
            onToken(null)
          },
          'error-callback': () => {
            if (!mountedRef.current) return
            onToken(null)
          }
        })
      } catch {
        onToken(null)
      }
    }

    setup()

    return () => {
      cancelled = true
    }
  }, [siteKey, onToken])

  return <div ref={containerRef} />
}
