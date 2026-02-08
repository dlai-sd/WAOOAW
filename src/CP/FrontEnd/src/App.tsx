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
import AgentDiscovery from './pages/AgentDiscovery'
import AgentDetail from './pages/AgentDetail'
import TrialDashboard from './pages/TrialDashboard'

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
                to="/"
                replace
                state={{ openAuth: true, nextPath: location.pathname + location.search }}
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
                to="/"
                replace
                state={{ openAuth: true, nextPath: location.pathname + location.search }}
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
                to="/"
                replace
                state={{ openAuth: true, nextPath: location.pathname + location.search }}
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
                to="/"
                replace
                state={{ openAuth: true, nextPath: location.pathname + location.search }}
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
