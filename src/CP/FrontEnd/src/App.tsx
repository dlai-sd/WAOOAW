import { useEffect, useState } from 'react'
import { Routes, Route, Navigate, useLocation, useNavigate, useParams } from 'react-router-dom'
import { FluentProvider } from '@fluentui/react-components'
import { Spinner } from '@fluentui/react-components'
import { waooawLightTheme, waooawDarkTheme } from './theme'
import { AuthProvider, useAuth } from './context/AuthContext'
import { PaymentsConfigProvider } from './context/PaymentsConfigContext'
import Header from './components/Header'
import LandingPage from './pages/LandingPage'
import AuthenticatedPortal from './pages/AuthenticatedPortal'
import AuthCallback from './pages/AuthCallback'
import SignIn from './pages/SignIn'
import SignUp from './pages/SignUp'
import AgentDiscovery from './pages/AgentDiscovery'
import AgentDetail from './pages/AgentDetail'
import TrialDashboard from './pages/TrialDashboard'
import HireSetupWizard from './pages/HireSetupWizard'
import HireReceipt from './pages/HireReceipt'

const HELP_BOXES_STORAGE_KEY = 'waooaw.cp.helpBoxesVisible'

function loadHelpBoxesPreference(): boolean {
  if (typeof window === 'undefined') return true
  const stored = window.localStorage.getItem(HELP_BOXES_STORAGE_KEY)
  return stored === null ? true : stored !== 'false'
}

// Wrapper that reads :agentId from the URL and opens the portal at agent-detail page.
// Must be a named component (not inline) so useParams is called inside a Route renderer.
function AgentDetailInPortal({
  theme,
  toggleTheme,
  showHelpBoxes,
  toggleHelpBoxes,
  handleLogout,
}: {
  theme: 'light' | 'dark'
  toggleTheme: () => void
  showHelpBoxes: boolean
  toggleHelpBoxes: () => void
  handleLogout: () => void
}) {
  const { agentId } = useParams<{ agentId: string }>()
  return (
    <AuthenticatedPortal
      theme={theme}
      toggleTheme={toggleTheme}
      showHelpBoxes={showHelpBoxes}
      toggleHelpBoxes={toggleHelpBoxes}
      onLogout={handleLogout}
      initialPage="agent-detail"
      initialAgentId={agentId}
    />
  )
}

function AppContent() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  const [showHelpBoxes, setShowHelpBoxes] = useState<boolean>(() => loadHelpBoxesPreference())
  const { isAuthenticated, isLoading, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/', { replace: true })
  }

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light')
  }

  const toggleHelpBoxes = () => {
    setShowHelpBoxes(prev => !prev)
  }

  useEffect(() => {
    window.localStorage.setItem(HELP_BOXES_STORAGE_KEY, String(showHelpBoxes))
  }, [showHelpBoxes])

  return (
    <FluentProvider theme={theme === 'light' ? waooawLightTheme : waooawDarkTheme}>
      <div className="app" data-help-boxes={showHelpBoxes ? 'visible' : 'hidden'}>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={
            isLoading ? (
              <>
                <Header theme={theme} toggleTheme={toggleTheme} showHelpBoxes={showHelpBoxes} toggleHelpBoxes={toggleHelpBoxes} />
                <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem 1rem' }}>
                  <Spinner size="large" />
                </div>
              </>
            ) : !isAuthenticated ? (
              <>
                <Header theme={theme} toggleTheme={toggleTheme} showHelpBoxes={showHelpBoxes} toggleHelpBoxes={toggleHelpBoxes} />
                <LandingPage />
              </>
            ) : (
              <Navigate to="/portal" replace />
            )
          } />
          <Route
            path="/signin"
            element={
              isLoading ? (
                <>
                  <Header theme={theme} toggleTheme={toggleTheme} showHelpBoxes={showHelpBoxes} toggleHelpBoxes={toggleHelpBoxes} />
                  <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem 1rem' }}>
                    <Spinner size="large" />
                  </div>
                </>
              ) : isAuthenticated ? (
                <Navigate to="/portal" replace />
              ) : (
                <SignIn theme={theme} toggleTheme={toggleTheme} showHelpBoxes={showHelpBoxes} toggleHelpBoxes={toggleHelpBoxes} />
              )
            }
          />
          <Route
            path="/signup"
            element={
              isLoading ? (
                <>
                  <Header theme={theme} toggleTheme={toggleTheme} showHelpBoxes={showHelpBoxes} toggleHelpBoxes={toggleHelpBoxes} />
                  <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem 1rem' }}>
                    <Spinner size="large" />
                  </div>
                </>
              ) : isAuthenticated ? (
                <Navigate to="/portal" replace />
              ) : (
                <SignUp theme={theme} toggleTheme={toggleTheme} showHelpBoxes={showHelpBoxes} toggleHelpBoxes={toggleHelpBoxes} />
              )
            }
          />
          <Route path="/auth/callback" element={<AuthCallback />} />

          {/* Protected routes */}
          <Route path="/portal" element={
            isLoading ? (
              <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem 1rem' }}>
                <Spinner size="large" />
              </div>
            ) : isAuthenticated ? (
              <AuthenticatedPortal theme={theme} toggleTheme={toggleTheme} showHelpBoxes={showHelpBoxes} toggleHelpBoxes={toggleHelpBoxes} onLogout={handleLogout} />
            ) : (
              <Navigate
                to={`/signin?next=${encodeURIComponent(location.pathname + location.search)}`}
                replace
              />
            )
          } />
          <Route path="/discover" element={
            isLoading ? (
              <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem 1rem' }}>
                <Spinner size="large" />
              </div>
            ) : isAuthenticated ? (
              <AuthenticatedPortal theme={theme} toggleTheme={toggleTheme} showHelpBoxes={showHelpBoxes} toggleHelpBoxes={toggleHelpBoxes} onLogout={handleLogout} initialPage="discover" />
            ) : (
              <Navigate
                to={`/signin?next=${encodeURIComponent(location.pathname + location.search)}`}
                replace
              />
            )
          } />
          <Route path="/my-agents" element={
            isLoading ? (
              <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem 1rem' }}>
                <Spinner size="large" />
              </div>
            ) : isAuthenticated ? (
              <AuthenticatedPortal theme={theme} toggleTheme={toggleTheme} showHelpBoxes={showHelpBoxes} toggleHelpBoxes={toggleHelpBoxes} onLogout={handleLogout} initialPage="my-agents" />
            ) : (
              <Navigate
                to={`/signin?next=${encodeURIComponent(location.pathname + location.search)}`}
                replace
              />
            )
          } />
          <Route path="/agent/:agentId" element={
            isLoading ? (
              <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem 1rem' }}>
                <Spinner size="large" />
              </div>
            ) : isAuthenticated ? (
              <AgentDetailInPortal theme={theme} toggleTheme={toggleTheme} showHelpBoxes={showHelpBoxes} toggleHelpBoxes={toggleHelpBoxes} handleLogout={handleLogout} />
            ) : (
              <Navigate
                to={`/signin?next=${encodeURIComponent(location.pathname + location.search)}`}
                replace
              />
            )
          } />
          <Route path="/trials" element={
            isLoading ? (
              <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem 1rem' }}>
                <Spinner size="large" />
              </div>
            ) : isAuthenticated ? (
              <>
                <Header theme={theme} toggleTheme={toggleTheme} showHelpBoxes={showHelpBoxes} toggleHelpBoxes={toggleHelpBoxes} />
                <TrialDashboard />
              </>
            ) : (
              <Navigate
                to={`/signin?next=${encodeURIComponent(location.pathname + location.search)}`}
                replace
              />
            )
          } />

          <Route path="/hire/setup/:subscriptionId" element={
            isLoading ? (
              <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem 1rem' }}>
                <Spinner size="large" />
              </div>
            ) : isAuthenticated ? (
              <>
                <Header theme={theme} toggleTheme={toggleTheme} showHelpBoxes={showHelpBoxes} toggleHelpBoxes={toggleHelpBoxes} />
                <HireSetupWizard />
              </>
            ) : (
              <Navigate
                to={`/signin?next=${encodeURIComponent(location.pathname + location.search)}`}
                replace
              />
            )
          } />

          <Route path="/hire/receipt/:orderId" element={
            isLoading ? (
              <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem 1rem' }}>
                <Spinner size="large" />
              </div>
            ) : isAuthenticated ? (
              <>
                <Header theme={theme} toggleTheme={toggleTheme} showHelpBoxes={showHelpBoxes} toggleHelpBoxes={toggleHelpBoxes} />
                <HireReceipt />
              </>
            ) : (
              <Navigate
                to={`/signin?next=${encodeURIComponent(location.pathname + location.search)}`}
                replace
              />
            )
          } />

          {/* Catch-all redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </FluentProvider>
  )
}

function App() {
  return (
    <AuthProvider>
      <PaymentsConfigProvider>
        <AppContent />
      </PaymentsConfigProvider>
    </AuthProvider>
  )
}

export default App
