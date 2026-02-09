import { Button } from '@fluentui/react-components'
import { WeatherMoon20Regular, WeatherSunny20Regular } from '@fluentui/react-icons'
import logoImage from '../Waooaw-Logo.png'
import { useNavigate } from 'react-router-dom'

interface HeaderProps {
  theme: 'light' | 'dark'
  toggleTheme: () => void
}

export default function Header({ theme, toggleTheme }: HeaderProps) {
  const navigate = useNavigate()

  return (
    <>
      <header className="header">
        <div className="container">
          <div className="header-content">
            <div className="logo">
              <img src={logoImage} alt="WAOOAW Logo" className="logo-image" />
            </div>
            <nav className="nav">
              <a href="#home">Home</a>
              <a href="#agents">Agents</a>
              <a href="#pricing">Pricing</a>
            </nav>
            <div className="header-actions">
              <Button 
                appearance="subtle" 
                icon={theme === 'light' ? <WeatherMoon20Regular /> : <WeatherSunny20Regular />}
                onClick={toggleTheme}
                aria-label="Toggle theme"
              />
              <Button appearance="outline" size="large" onClick={() => navigate('/signin')}>
                Sign In
              </Button>
              <Button appearance="primary" size="large" onClick={() => navigate('/signup')}>
                Sign Up
              </Button>
            </div>
          </div>
        </div>
      </header>
    </>
  )
}
