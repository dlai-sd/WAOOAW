import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Button, Text } from '@fluentui/react-components'
import { 
  Home24Regular, 
  Bot24Regular, 
  People24Regular, 
  Money24Regular,
  Database24Regular,
  ShieldTask24Regular,
  Certificate24Regular,
  Beaker24Regular,
  WeatherMoon24Regular,
  WeatherSunny24Regular,
  SignOut24Regular
} from '@fluentui/react-icons'
import waooawLogo from '../Waooaw-Logo.png'

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
    { path: '/agent-setup', label: 'Agent Setup', icon: <Bot24Regular /> },
    { path: '/review-queue', label: 'Review Queue', icon: <ShieldTask24Regular /> },
    { path: '/hired-agents', label: 'Hired Agents', icon: <People24Regular /> },
    { path: '/customers', label: 'Customers', icon: <People24Regular /> },
    { path: '/billing', label: 'Billing', icon: <Money24Regular /> },
    { path: '/db-updates', label: 'DB Updates', icon: <Database24Regular /> },
    { path: '/audit', label: 'Audit', icon: <ShieldTask24Regular /> },
    { path: '/policy-denials', label: 'Policy Denials', icon: <ShieldTask24Regular /> },
    { path: '/agent-spec-tools', label: 'AgentSpec Tools', icon: <Certificate24Regular /> },
    { path: '/governor', label: 'Governor', icon: <ShieldTask24Regular /> },
    { path: '/reference-agents', label: 'Reference Agents', icon: <Beaker24Regular /> },
    { path: '/genesis', label: 'Genesis', icon: <Certificate24Regular /> },
  ]

  return (
    <div className="layout">
      <nav className="sidebar">
        <div className="sidebar-header">
          <img src={waooawLogo} alt="WAOOAW Logo" className="sidebar-logo-image" />
          <Text size={200}>Platform Portal</Text>
        </div>

        <div className="nav-items">
          {navItems.map(item => (
            (() => {
              const active = item.path === '/' ? location.pathname === '/' : location.pathname.startsWith(item.path)
              return (
            <Link 
              key={item.path} 
              to={item.path} 
              className={`nav-item ${active ? 'active' : ''}`}
            >
              {item.icon}
              <span>{item.label}</span>
            </Link>
              )
            })()
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
