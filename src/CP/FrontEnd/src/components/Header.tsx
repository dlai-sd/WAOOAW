import { Button } from '@fluentui/react-components'
import { WeatherMoon20Regular, WeatherSunny20Regular } from '@fluentui/react-icons'
import logoImage from '../Waooaw-Logo.png'
import { useNavigate } from 'react-router-dom'

interface HeaderProps {
  theme: 'light' | 'dark'
  toggleTheme: () => void
  showHelpBoxes: boolean
  toggleHelpBoxes: () => void
}

export default function Header({ theme, toggleTheme, showHelpBoxes, toggleHelpBoxes }: HeaderProps) {
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
                className="header-help-toggle"
                appearance="subtle"
                onClick={toggleHelpBoxes}
                aria-label={showHelpBoxes ? 'Hide help boxes' : 'Show help boxes'}
                data-testid="cp-help-toggle"
                size="medium"
              >
                {showHelpBoxes ? 'Hide Help' : 'Show Help'}
              </Button>
              <Button 
                className="header-theme-toggle"
                appearance="subtle" 
                icon={theme === 'light' ? <WeatherMoon20Regular /> : <WeatherSunny20Regular />}
                onClick={toggleTheme}
                aria-label="Toggle theme"
                size="medium"
              />
              <Button className="header-cta header-cta--secondary" appearance="outline" size="medium" onClick={() => navigate('/signin')}>
                Sign In
              </Button>
              <Button className="header-cta header-cta--primary" appearance="primary" size="medium" onClick={() => navigate('/signup')}>
                Sign Up
              </Button>
            </div>
          </div>
        </div>
      </header>
    </>
  )
}
