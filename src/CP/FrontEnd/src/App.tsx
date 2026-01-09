import { useState } from 'react'
import { FluentProvider } from '@fluentui/react-components'
import { waooawLightTheme, waooawDarkTheme } from './theme'
import { AuthProvider, useAuth } from './context/AuthContext'
import Header from './components/Header'
import LandingPage from './pages/LandingPage'
import AuthenticatedPortal from './pages/AuthenticatedPortal'
import AuthCallback from './pages/AuthCallback'

function AppContent() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  const { isAuthenticated, logout } = useAuth()

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light')
  }

  // Check if we're on the auth callback route
  const isCallbackRoute = window.location.pathname === '/auth/callback'

  if (isCallbackRoute) {
    return <AuthCallback />
  }

  return (
    <FluentProvider theme={theme === 'light' ? waooawLightTheme : waooawDarkTheme}>
      <div className="app">
        {!isAuthenticated ? (
          <>
            <Header theme={theme} toggleTheme={toggleTheme} />
            <LandingPage />
          </>
        ) : (
          <AuthenticatedPortal theme={theme} toggleTheme={toggleTheme} onLogout={logout} />
        )}
      </div>
    </FluentProvider>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App
