import { useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { FluentProvider } from '@fluentui/react-components'
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
  const { isAuthenticated, logout } = useAuth()

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light')
  }

  return (
    <FluentProvider theme={theme === 'light' ? waooawLightTheme : waooawDarkTheme}>
      <div className="app">
        <Routes>
          {/* Public routes */}
          <Route path="/" element={
            !isAuthenticated ? (
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
            isAuthenticated ? (
              <AuthenticatedPortal theme={theme} toggleTheme={toggleTheme} onLogout={logout} />
            ) : (
              <Navigate to="/" replace />
            )
          } />
          <Route path="/discover" element={
            isAuthenticated ? (
              <>
                <Header theme={theme} toggleTheme={toggleTheme} />
                <AgentDiscovery />
              </>
            ) : (
              <Navigate to="/" replace />
            )
          } />
          <Route path="/agent/:id" element={
            isAuthenticated ? (
              <>
                <Header theme={theme} toggleTheme={toggleTheme} />
                <AgentDetail />
              </>
            ) : (
              <Navigate to="/" replace />
            )
          } />
          <Route path="/trials" element={
            isAuthenticated ? (
              <>
                <Header theme={theme} toggleTheme={toggleTheme} />
                <TrialDashboard />
              </>
            ) : (
              <Navigate to="/" replace />
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
