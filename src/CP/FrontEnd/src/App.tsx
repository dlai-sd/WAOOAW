import { useState } from 'react'
import { FluentProvider } from '@fluentui/react-components'
import { waooawLightTheme, waooawDarkTheme } from './theme'
import Header from './components/Header'
import LandingPage from './pages/LandingPage'
import AuthenticatedPortal from './pages/AuthenticatedPortal'

function App() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light')
  }

  const handleLogin = () => {
    setIsAuthenticated(true)
  }

  const handleLogout = () => {
    setIsAuthenticated(false)
  }

  return (
    <FluentProvider theme={theme === 'light' ? waooawLightTheme : waooawDarkTheme}>
      <div className="app">
        {!isAuthenticated ? (
          <>
            <Header theme={theme} toggleTheme={toggleTheme} onLogin={handleLogin} />
            <LandingPage />
          </>
        ) : (
          <AuthenticatedPortal theme={theme} toggleTheme={toggleTheme} onLogout={handleLogout} />
        )}
      </div>
    </FluentProvider>
  )
}

export default App
