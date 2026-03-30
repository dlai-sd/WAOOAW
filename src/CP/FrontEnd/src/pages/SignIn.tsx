import { useMemo } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import Header from '../components/Header'
import AuthPanel from '../components/auth/AuthPanel'
import { Button } from '@fluentui/react-components'
import { Dismiss24Regular } from '@fluentui/react-icons'

type SignInProps = {
  theme: 'light' | 'dark'
  toggleTheme: () => void
}

function sanitizeNextPath(raw: string | null): string | null {
  if (!raw) return null
  if (!raw.startsWith('/')) return null
  if (raw.startsWith('//')) return null
  return raw
}

const LEFT_PANEL = {
  illustration: '',
  heading: 'Welcome back.',
  tagline: 'Your AI workforce is ready to run.',
  bullets: [
    '✅ 7-day free trial — no credit card needed',
    '✅ Keep all deliverables, even if you cancel',
    '✅ Access 19+ specialised AI agents instantly',
    '✅ Passwordless — sign in with email OTP or Google',
  ],
  footnote: 'Join hundreds of businesses already saving hours every week.',
}

const SIGNIN_PROOF = [
  { value: '19+', label: 'Specialised agents' },
  { value: '1', label: 'Unified customer OS' },
  { value: '24/7', label: 'Always-on workforce' },
]

export default function SignIn({ theme, toggleTheme }: SignInProps) {
  const location = useLocation()
  const navigate = useNavigate()

  const nextPath = useMemo(() => {
    const params = new URLSearchParams(location.search)
    return sanitizeNextPath(params.get('next'))
  }, [location.search])

  const p = LEFT_PANEL

  return (
    <>
      <Header theme={theme} toggleTheme={toggleTheme} />
      <main className="auth-page auth-page--signin" data-testid="cp-signin-page">
        <div className="auth-center">
          <div className="auth-unified-card auth-unified-card--wide auth-unified-card--signin">

            {/* Single card-level title + close */}
            <div className="auth-unified-header">
              <h1 className="auth-unified-title">Sign in to WAOOAW</h1>
              <Button
                appearance="subtle"
                aria-label="Close"
                data-testid="cp-signin-close"
                icon={<Dismiss24Regular />}
                onClick={() => navigate('/', { replace: true })}
              />
            </div>

            {/* Body: left copy | divider | right form */}
            <div className="auth-unified-body">

              {/* Left — static engaging copy */}
              <section className="auth-left-panel" aria-label="Why use WAOOAW">
                <div className="auth-left-step">
                  <div className="auth-left-illustration">{p.illustration}</div>
                  <div className="auth-side-kicker">Customer Command Centre</div>
                  <h2 className="auth-left-heading">{p.heading}</h2>
                  <p className="auth-left-tagline">{p.tagline}</p>
                  <div className="auth-proof-grid">
                    {SIGNIN_PROOF.map((item) => (
                      <div key={item.label} className="auth-proof-card">
                        <div className="auth-proof-value">{item.value}</div>
                        <div className="auth-proof-label">{item.label}</div>
                      </div>
                    ))}
                  </div>
                  <ul className="auth-left-bullets">
                    {p.bullets.map((b) => (
                      <li key={b}>{b}</li>
                    ))}
                  </ul>
                  <p className="auth-left-footnote">{p.footnote}</p>
                </div>
              </section>

              {/* Vertical divider */}
              <div className="auth-panel-divider" aria-hidden="true" />

              {/* Right — form (embedded: no card chrome, no duplicate title) */}
              <div className="auth-right-panel">
                <AuthPanel
                  theme={theme}
                  initialMode="signin"
                  embedded
                  showCloseButton={false}
                  onClose={() => navigate('/', { replace: true })}
                  onSuccess={() => navigate(nextPath || '/portal', { replace: true })}
                  onRequestSignUp={() => {
                    const dest = nextPath ? `/signup?next=${encodeURIComponent(nextPath)}` : '/signup'
                    navigate(dest)
                  }}
                />
              </div>

            </div>
          </div>
        </div>
      </main>
    </>
  )
}
