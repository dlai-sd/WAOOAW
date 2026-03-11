import { useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import Header from '../components/Header'
import AuthPanel from '../components/auth/AuthPanel'
import { Button } from '@fluentui/react-components'
import { Dismiss24Regular } from '@fluentui/react-icons'

type SignUpProps = {
  theme: 'light' | 'dark'
  toggleTheme: () => void
}

function sanitizeNextPath(raw: string | null): string | null {
  if (!raw) return null
  if (!raw.startsWith('/')) return null
  if (raw.startsWith('//')) return null
  return raw
}

const STEP_CONTENT: Record<1 | 2 | 3, {
  illustration: string
  heading: string
  tagline: string
  bullets: string[]
  footnote: string
}> = {
  1: {
    illustration: '',
    heading: 'Start free. Keep everything.',
    tagline: 'Zero risk. Real results.',
    bullets: [
      '✅ 7-day free trial — no credit card needed',
      '✅ Keep all deliverables, even if you cancel',
      '✅ Access 19+ specialised AI agents instantly',
      '✅ Passwordless — sign in with email OTP or Google',
    ],
    footnote: 'Join hundreds of businesses already saving hours every week.',
  },
  2: {
    illustration: '🤝',
    heading: 'Meet your AI workforce.',
    tagline: 'Agents built for your industry.',
    bullets: [
      '📢 Marketing — content, SEO, social, email, PPC',
      '🎓 Education — tutoring, test prep, career coaching',
      '💼 Sales — lead gen, SDR, CRM, account management',
      '⚙️ Technology, Healthcare, Finance & more',
    ],
    footnote: 'Telling us your industry helps us show the most relevant agents first.',
  },
  3: {
    illustration: '⚡',
    heading: "You're 30 seconds away.",
    tagline: 'Your AI team is ready to go.',
    bullets: [
      '💬 Agents reach you on your preferred channel',
      '📊 Track outcomes in your portal dashboard',
      '🔄 Swap agents anytime — no lock-in',
      '🛡️ Your data is encrypted and never sold',
    ],
    footnote: 'After you verify your email, your 7-day trial begins immediately.',
  },
}

export default function SignUp({ theme, toggleTheme }: SignUpProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const [regStep, setRegStep] = useState<1 | 2 | 3>(1)

  const nextPath = useMemo(() => {
    const params = new URLSearchParams(location.search)
    return sanitizeNextPath(params.get('next'))
  }, [location.search])

  const step = STEP_CONTENT[regStep]
  const registrationMilestones = ['Create account', 'Describe business', 'Launch first agent trial']

  return (
    <>
      <Header theme={theme} toggleTheme={toggleTheme} />
      <main className="auth-page">
        <div className="auth-center">
          <div className="auth-unified-card">

            {/* Single card-level title + close — no competing headers */}
            <div className="auth-unified-header">
              <h1 className="auth-unified-title">Create your WAOOAW account</h1>
              <Button
                appearance="subtle"
                aria-label="Close"
                icon={<Dismiss24Regular />}
                onClick={() => navigate('/', { replace: true })}
              />
            </div>

            {/* Body: left copy | divider | right form */}
            <div className="auth-unified-body">

              {/* Left — step-reactive engaging copy */}
              <section className="auth-left-panel" aria-label="Why create an account">
                <div className="auth-left-step" key={regStep}>
                  <div className="auth-left-illustration">{step.illustration}</div>
                  <div className="auth-side-kicker">Start Your Workforce</div>
                  <h2 className="auth-left-heading">{step.heading}</h2>
                  <p className="auth-left-tagline">{step.tagline}</p>
                  <div className="auth-milestone-list">
                    {registrationMilestones.map((milestone, index) => (
                      <div key={milestone} className={`auth-milestone-item ${regStep === index + 1 ? 'active' : ''}`}>
                        <span className="auth-milestone-index">0{index + 1}</span>
                        <span>{milestone}</span>
                      </div>
                    ))}
                  </div>
                  <ul className="auth-left-bullets">
                    {step.bullets.map((b) => (
                      <li key={b}>{b}</li>
                    ))}
                  </ul>
                  <p className="auth-left-footnote">{step.footnote}</p>
                  <div className="auth-confidence-card">
                    <div className="auth-confidence-title">Why this matters</div>
                    <p className="auth-confidence-body">
                      Signup should explain the value ladder: try first, keep the work, then decide whether this agent
                      deserves a bigger role in the business.
                    </p>
                  </div>
                </div>
              </section>

              {/* Vertical divider */}
              <div className="auth-panel-divider" aria-hidden="true" />

              {/* Right — form (embedded: no card chrome, no duplicate title) */}
              <div className="auth-right-panel">
                <AuthPanel
                  theme={theme}
                  initialMode="register"
                  embedded
                  showCloseButton={false}
                  onClose={() => navigate('/', { replace: true })}
                  onSuccess={() => navigate(nextPath || '/portal', { replace: true })}
                  onRequestSignIn={() => {
                    const dest = nextPath ? `/signin?next=${encodeURIComponent(nextPath)}` : '/signin'
                    navigate(dest)
                  }}
                  onStepChange={(s) => setRegStep(s)}
                />
              </div>

            </div>

          </div>
        </div>
      </main>
    </>
  )
}
