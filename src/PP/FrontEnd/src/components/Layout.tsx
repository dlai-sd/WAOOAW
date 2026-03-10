import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Button, Text } from '@fluentui/react-components'
import { 
  Home24Regular, 
  Bot24Regular, 
  People24Regular, 
  Money24Regular,
  Database24Regular,
  Certificate24Regular,
  Beaker24Regular,
  WeatherMoon24Regular,
  WeatherSunny24Regular,
  SignOut24Regular,
  DocumentCheckmark24Regular,
  DocumentEdit24Regular,
  ClipboardTask24Regular,
  AlertBadge24Regular,
} from '@fluentui/react-icons'
import waooawLogo from '../Waooaw-Logo.png'

interface LayoutProps {
  children: ReactNode
  theme: 'light' | 'dark'
  onThemeToggle: () => void
  onLogout: () => void
}

type NavItem =
  | { type?: undefined; path: string; label: string; icon: ReactNode }
  | { type: 'section'; label: string }

const navItems: NavItem[] = [
  { type: 'section', label: 'Operations' },
  { path: '/', label: 'Dashboard', icon: <Home24Regular /> },
  { path: '/hired-agents', label: 'Hired Agents', icon: <People24Regular /> },
  { path: '/customers', label: 'Usage Events', icon: <Database24Regular /> },
  { path: '/billing', label: 'Subscriptions', icon: <Money24Regular /> },
  { type: 'section', label: 'Management' },
  { path: '/agents', label: 'Agent Management', icon: <Bot24Regular /> },
  { path: '/agent-setup', label: 'Agent Setup', icon: <Bot24Regular /> },
  { path: '/agent-type-setup', label: 'Agent Type Setup', icon: <Certificate24Regular /> },
  { path: '/governor', label: 'Reference Agents', icon: <Beaker24Regular /> },
  { path: '/genesis', label: 'Genesis', icon: <Certificate24Regular /> },
  { type: 'section', label: 'Compliance' },
  { path: '/approvals-queue', label: 'Approvals Queue', icon: <DocumentCheckmark24Regular /> },
  { path: '/review-queue', label: 'Draft Review', icon: <DocumentEdit24Regular /> },
  { path: '/audit', label: 'Audit', icon: <ClipboardTask24Regular /> },
  { path: '/policy-denials', label: 'Policy Denials', icon: <AlertBadge24Regular /> },
  { type: 'section', label: 'Tools' },
  { path: '/agent-spec-tools', label: 'AgentSpec Tools', icon: <Certificate24Regular /> },
  { path: '/db-updates', label: 'DB Updates', icon: <Database24Regular /> },
  { path: '/reference-agents', label: 'Reference Data', icon: <Beaker24Regular /> },
]

export default function Layout({ children, theme, onThemeToggle, onLogout }: LayoutProps) {
  const location = useLocation()

  return (
    <div className="layout">
      <nav className="sidebar">
        <div className="sidebar-header">
          <img src={waooawLogo} alt="WAOOAW Logo" className="sidebar-logo-image" />
          <Text size={200}>Platform Portal</Text>
        </div>

        <div className="nav-items">
          {navItems.map((item, idx) => {
            if (item.type === 'section') {
              return (
                <Text
                  key={`section-${idx}`}
                  size={100}
                  style={{ padding: '12px 16px 4px', color: 'var(--colorNeutralForeground3)', textTransform: 'uppercase', letterSpacing: '0.08em' }}
                >
                  {item.label}
                </Text>
              )
            }
            const active = item.path === '/' ? location.pathname === '/' : location.pathname.startsWith(item.path)
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`nav-item ${active ? 'active' : ''}`}
                data-testid={`pp-nav-${item.label.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')}`}
              >
                {item.icon}
                <span>{item.label}</span>
              </Link>
            )
          })}
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
            data-testid="pp-logout-button"
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
