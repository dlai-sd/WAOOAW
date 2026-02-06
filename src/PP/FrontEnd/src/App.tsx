import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { FluentProvider, Spinner, Button, Dialog, DialogSurface, DialogBody, DialogTitle, DialogContent, Text } from '@fluentui/react-components'
import { GoogleOAuthProvider, GoogleLogin, CredentialResponse } from '@react-oauth/google'
import { WeatherMoon24Regular, WeatherSunny24Regular } from '@fluentui/react-icons'
import { waooawDarkTheme, waooawLightTheme } from './theme'
import { AuthProvider, consumeAuthExpiredFlag, useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import LandingPage from './pages/LandingPage'
import Dashboard from './pages/Dashboard'
import AgentManagement from './pages/AgentManagement'
import AgentData from './pages/AgentData'
import CustomerManagement from './pages/CustomerManagement'
import Billing from './pages/Billing'
import GovernorConsole from './pages/GovernorConsole'
import ReferenceAgents from './pages/ReferenceAgents'
import GenesisConsole from './pages/GenesisConsole'
import AuditConsole from './pages/AuditConsole'
import DbUpdates from './pages/DbUpdates'
import config from './config/oauth.config'
import { API_ENDPOINTS } from './config/oauth.config'
import waooawLogo from './Waooaw-Logo.png'
import './styles/globals.css'

function AppShell() {
  const [theme, setTheme] = useState<'light' | 'dark'>('dark')
  const [showLoginDialog, setShowLoginDialog] = useState(false)
  const { isAuthenticated, isLoading, login, logout } = useAuth()

  useEffect(() => {
    if (!isAuthenticated && consumeAuthExpiredFlag()) {
      setShowLoginDialog(true)
    }
  }, [isAuthenticated])

  const handleGoogleSuccess = async (credentialResponse: CredentialResponse) => {
    if (credentialResponse.credential) {
      const res = await fetch(API_ENDPOINTS.googleVerify, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credential: credentialResponse.credential })
      })

      if (!res.ok) {
        const body = await res.text()
        throw new Error(body || 'Authentication failed')
      }

      const data = await res.json()
      await login(data.access_token)
      setShowLoginDialog(false)
    }
  }

  const handleGoogleError = () => {
    console.error('Google login failed')
  }

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light')
  }

  const handleLoginClick = () => {
    setShowLoginDialog(true)
  }

  const handleDemoLogin = async () => {
    const res = await fetch(`${config.apiBaseUrl}/auth/dev-token`, { method: 'POST' })
    if (!res.ok) {
      const body = await res.text()
      throw new Error(body || 'Demo login failed')
    }
    const data = await res.json()
    await login(data.access_token)
    setShowLoginDialog(false)
  }

  const allowDemoLogin = config.name === 'codespace' || config.name === 'development'

  return (
    <FluentProvider theme={theme === 'light' ? waooawLightTheme : waooawDarkTheme}>
      <div data-theme={theme}>
        {isLoading ? (
        <div className="app-shell">
          <main className="app-main">
            <Spinner label="Loading..." />
          </main>
        </div>
      ) : !isAuthenticated ? (
        <div className="app-shell-landing">
          <header className="header">
            <div className="container">
              <div className="header-content">
                <div className="logo">
                  <img src={waooawLogo} alt="WAOOAW Logo" className="logo-image" />
                </div>
                <div className="header-actions">
                  <Button 
                    appearance="subtle" 
                    icon={theme === 'light' ? <WeatherMoon24Regular /> : <WeatherSunny24Regular />}
                    onClick={toggleTheme}
                    aria-label="Toggle theme"
                  />
                  <Button appearance="primary" onClick={handleLoginClick}>
                    Sign In
                  </Button>
                </div>
              </div>
            </div>
          </header>
          <main>
            <LandingPage />
          </main>

          <Dialog open={showLoginDialog} onOpenChange={(_, data) => setShowLoginDialog(data.open)}>
            <DialogSurface>
              <DialogBody>
                <DialogTitle>Sign in to Platform Portal</DialogTitle>
                <DialogContent>
                  <div style={{ padding: '16px 0', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {config.googleClientId ? (
                      <GoogleLogin onSuccess={handleGoogleSuccess} onError={handleGoogleError} />
                    ) : (
                      <>
                        <Button appearance="primary" style={{ width: '100%' }} disabled>
                          Continue with Google
                        </Button>
                        <Text size={200} style={{ opacity: 0.9 }}>
                          {allowDemoLogin ? (
                            <>
                              Google Sign-In is not configured for this environment (missing client ID). Use Demo Login, or set{' '}
                              <strong>VITE_GOOGLE_CLIENT_ID</strong> and rebuild the frontend.
                            </>
                          ) : (
                            <>
                              Google Sign-In is not configured for this environment (missing client ID). Set{' '}
                              <strong>VITE_GOOGLE_CLIENT_ID</strong> and rebuild the frontend.
                            </>
                          )}
                        </Text>
                      </>
                    )}

                    {allowDemoLogin && (
                      <>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <div style={{ flex: 1, height: '1px', background: 'var(--colorNeutralStroke2)' }}></div>
                          <Text size={200}>OR</Text>
                          <div style={{ flex: 1, height: '1px', background: 'var(--colorNeutralStroke2)' }}></div>
                        </div>

                        <Button 
                          appearance="secondary" 
                          style={{ width: '100%' }}
                          onClick={handleDemoLogin}
                        >
                          Demo Login (Skip OAuth)
                        </Button>
                      </>
                    )}
                  </div>
                  <Text size={200} style={{ display: 'block', marginTop: '12px', opacity: 0.8 }}>
                    {allowDemoLogin
                      ? 'Use your WAOOAW Google account to access the platform console, or use demo login to preview.'
                      : 'Use your WAOOAW Google account to access the platform console.'}
                  </Text>
                </DialogContent>
              </DialogBody>
            </DialogSurface>
          </Dialog>
        </div>
      ) : (
        <BrowserRouter>
          <Layout theme={theme} onThemeToggle={toggleTheme} onLogout={logout}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/agents" element={<AgentManagement />} />
              <Route path="/agents/data" element={<AgentData />} />
              <Route path="/customers" element={<CustomerManagement />} />
              <Route path="/billing" element={<Billing />} />
              <Route path="/db-updates" element={<DbUpdates />} />
              <Route path="/audit" element={<AuditConsole />} />
              <Route path="/governor" element={<GovernorConsole />} />
              <Route path="/reference-agents" element={<ReferenceAgents />} />
              <Route path="/genesis" element={<GenesisConsole />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Layout>
        </BrowserRouter>
      )}
      </div>
    </FluentProvider>
  )
}

function App() {
  const app = (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  )

  return config.googleClientId ? <GoogleOAuthProvider clientId={config.googleClientId}>{app}</GoogleOAuthProvider> : app
}

export default App
