import { useMemo } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import Header from '../components/Header'
import AuthPanel from '../components/auth/AuthPanel'
import { Button } from '@fluentui/react-components'

type SignUpProps = {
  theme: 'light' | 'dark'
  toggleTheme: () => void
}

function sanitizeNextPath(raw: string | null): string | null {
  if (!raw) return null
  if (!raw.startsWith('/')) return null
  // Avoid open-redirects. Keep it internal-only.
  if (raw.startsWith('//')) return null
  return raw
}

export default function SignUp({ theme, toggleTheme }: SignUpProps) {
  const location = useLocation()
  const navigate = useNavigate()

  const nextPath = useMemo(() => {
    const params = new URLSearchParams(location.search)
    return sanitizeNextPath(params.get('next'))
  }, [location.search])

  return (
    <>
      <Header theme={theme} toggleTheme={toggleTheme} />
      <main className="auth-page">
        <div className="container">
          <div className="auth-split">
            <section className="auth-side" aria-label="Why create an account">
              <h1>Join the WAOOAW Customer Portal</h1>
              <p>
                Create your account to start a 7-day trial and keep the deliverables. You can sign in with Google or use a
                passwordless email OTP.
              </p>
              <p style={{ marginTop: '12px' }}>
                Once you’re in, browse agents like talent — compare specialties, start a trial, and track outcomes.
              </p>
            </section>

            <div className="auth-form">
              <div className="auth-stack">
                <AuthPanel
                  theme={theme}
                  initialMode="register"
                  showCloseButton
                  onClose={() => navigate('/', { replace: true })}
                  onSuccess={() => navigate(nextPath || '/portal', { replace: true })}
                  onRequestSignIn={() => {
                    const dest = nextPath ? `/signin?next=${encodeURIComponent(nextPath)}` : '/signin'
                    navigate(dest)
                  }}
                />
                <div className="auth-close-row">
                  <Button appearance="secondary" onClick={() => navigate('/', { replace: true })}>
                    Close
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </>
  )
}
