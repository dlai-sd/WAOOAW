import { Button } from '@fluentui/react-components'
import { WeatherMoon20Regular, WeatherSunny20Regular } from '@fluentui/react-icons'
import logoImage from '../Waooaw-Logo.png'

interface HeaderProps {
  theme: 'light' | 'dark'
  toggleTheme: () => void
  onLogin?: () => void
}

export default function Header({ theme, toggleTheme, onLogin }: HeaderProps) {
  return (
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
            <Button appearance="outline" onClick={onLogin}>Sign In</Button>
          </div>
        </div>
      </div>
    </header>
  )
}
