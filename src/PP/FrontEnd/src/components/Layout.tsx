import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Button, Text } from '@fluentui/react-components'
import { 
  Home24Regular, 
  Bot24Regular, 
  People24Regular, 
  Money24Regular,
  ShieldTask24Regular,
  Certificate24Regular,
  WeatherMoon24Regular,
  WeatherSunny24Regular,
  SignOut24Regular
} from '@fluentui/react-icons'

interface LayoutProps {
  children: ReactNode
  theme: 'light' | 'dark'
  onThemeToggle: () => void
  onLogout: () => void
}

export default function Layout({ children, theme, onThemeToggle, onLogout }: LayoutProps) {
  const location = useLocation()

  const navItems = [
    { path: '/', label: 'Dashboard', icon: <Home24Regular /> },
    { path: '/agents', label: 'Agent Management', icon: <Bot24Regular /> },
    { path: '/customers', label: 'Customers', icon: <People24Regular /> },
    { path: '/billing', label: 'Billing', icon: <Money24Regular /> },
    { path: '/governor', label: 'Governor', icon: <ShieldTask24Regular /> },
    { path: '/genesis', label: 'Genesis', icon: <Certificate24Regular /> },
  ]

  return (
    <div className="layout">
      <nav className="sidebar">
        <div className="sidebar-header">
          <Text size={600} weight="semibold">WAOOAW</Text>
          <Text size={200}>Platform Portal</Text>
        </div>

        <div className="nav-items">
          {navItems.map(item => (
            <Link 
              key={item.path} 
              to={item.path} 
              className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
            >
              {item.icon}
              <span>{item.label}</span>
            </Link>
          ))}
        </div>

        <div className="sidebar-footer">
          <Button 
            appearance="subtle" 
            icon={theme === 'light' ? <WeatherMoon24Regular /> : <WeatherSunny24Regular />}
            onClick={onThemeToggle}
            style={{ width: '100%', justifyContent: 'flex-start' }}
          >
            {theme === 'light' ? 'Dark' : 'Light'} Mode
          </Button>
          <Button 
            appearance="subtle" 
            icon={<SignOut24Regular />}
            onClick={onLogout}
            style={{ width: '100%', justifyContent: 'flex-start' }}
          >
            Logout
          </Button>
        </div>
      </nav>

      <main className="main-content">
        {children}
      </main>
    </div>
  )
}
