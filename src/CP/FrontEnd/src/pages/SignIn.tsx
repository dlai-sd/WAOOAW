import { useMemo } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import Header from '../components/Header'
import AuthPanel from '../components/auth/AuthPanel'

type SignInProps = {
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

export default function SignIn({ theme, toggleTheme }: SignInProps) {
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
          <div className="auth-center">
            <AuthPanel
              theme={theme}
              initialMode="signin"
              onSuccess={() => navigate(nextPath || '/portal', { replace: true })}
              onRequestSignUp={() => {
                const dest = nextPath ? `/signup?next=${encodeURIComponent(nextPath)}` : '/signup'
                navigate(dest)
              }}
            />
          </div>
        </div>
      </main>
    </>
  )
}
