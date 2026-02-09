import { useState } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
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

function AppContent() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  const { isAuthenticated, isLoading, logout } = useAuth()
  const location = useLocation()

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light')
  }

  return (
    <FluentProvider theme={theme === 'light' ? waooawLightTheme : waooawDarkTheme}>
      <div className="app">
        <Routes>
          {/* Public routes */}
          <Route path="/" element={
            isLoading ? (
              <>
                <Header theme={theme} toggleTheme={toggleTheme} />
                <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem 1rem' }}>
                  <Spinner size="large" />
                </div>
              </>
            ) : !isAuthenticated ? (
              <>
                <Header theme={theme} toggleTheme={toggleTheme} />
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
                  <Header theme={theme} toggleTheme={toggleTheme} />
                  <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem 1rem' }}>
                    <Spinner size="large" />
                  </div>
                </>
              ) : isAuthenticated ? (
                <Navigate to="/portal" replace />
              ) : (
                <SignIn theme={theme} toggleTheme={toggleTheme} />
              )
            }
          />
          <Route
            path="/signup"
            element={
              isLoading ? (
                <>
                  <Header theme={theme} toggleTheme={toggleTheme} />
                  <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem 1rem' }}>
                    <Spinner size="large" />
                  </div>
                </>
              ) : isAuthenticated ? (
                <Navigate to="/portal" replace />
              ) : (
                <SignUp theme={theme} toggleTheme={toggleTheme} />
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
              <AuthenticatedPortal theme={theme} toggleTheme={toggleTheme} onLogout={logout} />
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
              <>
                <Header theme={theme} toggleTheme={toggleTheme} />
                <AgentDiscovery />
              </>
            ) : (
              <Navigate
                to={`/signin?next=${encodeURIComponent(location.pathname + location.search)}`}
                replace
              />
            )
          } />
          <Route path="/agent/:id" element={
            isLoading ? (
              <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem 1rem' }}>
                <Spinner size="large" />
              </div>
            ) : isAuthenticated ? (
              <>
                <Header theme={theme} toggleTheme={toggleTheme} />
                <AgentDetail />
              </>
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
                <Header theme={theme} toggleTheme={toggleTheme} />
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
                <Header theme={theme} toggleTheme={toggleTheme} />
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
                <Header theme={theme} toggleTheme={toggleTheme} />
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
