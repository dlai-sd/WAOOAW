import { useState } from 'react'
import { Button } from '@fluentui/react-components'
import { 
  WeatherMoon20Regular, 
  WeatherSunny20Regular,
  Home20Regular,
  Bot20Regular,
  Target20Regular,
  CheckboxChecked20Regular,
  DataBarVertical20Regular,
  Payment20Regular,
  PhoneDesktop20Regular,
  Alert20Regular,
  Settings20Regular,
  QuestionCircle20Regular,
  SignOut20Regular
} from '@fluentui/react-icons'
import logoImage from '../Waooaw-Logo.png'
import Dashboard from './authenticated/Dashboard'
import MyAgents from './authenticated/MyAgents'
import Approvals from './authenticated/Approvals'
import GoalsSetup from './authenticated/GoalsSetup'
import Performance from './authenticated/Performance'
import UsageBilling from './authenticated/UsageBilling'

interface AuthenticatedPortalProps {
  theme: 'light' | 'dark'
  toggleTheme: () => void
  onLogout: () => void
}

type Page = 'dashboard' | 'my-agents' | 'goals' | 'approvals' | 'performance' | 'billing' | 'mobile' | 'notifications' | 'settings' | 'help'

export default function AuthenticatedPortal({ theme, toggleTheme, onLogout }: AuthenticatedPortalProps) {
  const [currentPage, setCurrentPage] = useState<Page>('dashboard')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  const pendingApprovalsCount = 3 // Mock data

  const menuItems = [
    { id: 'dashboard' as Page, icon: <Home20Regular />, label: 'Dashboard' },
    { id: 'my-agents' as Page, icon: <Bot20Regular />, label: 'My Agents' },
    { id: 'goals' as Page, icon: <Target20Regular />, label: 'Goals & Setup' },
    { id: 'approvals' as Page, icon: <CheckboxChecked20Regular />, label: 'Approvals', badge: pendingApprovalsCount },
    { id: 'performance' as Page, icon: <DataBarVertical20Regular />, label: 'Performance' },
    { id: 'billing' as Page, icon: <Payment20Regular />, label: 'Usage & Billing' },
    { id: 'mobile' as Page, icon: <PhoneDesktop20Regular />, label: 'Mobile App' },
    { id: 'notifications' as Page, icon: <Alert20Regular />, label: 'Notifications' },
    { id: 'settings' as Page, icon: <Settings20Regular />, label: 'Settings' },
    { id: 'help' as Page, icon: <QuestionCircle20Regular />, label: 'Help & Support' },
  ]

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />
      case 'my-agents':
        return <MyAgents />
      case 'approvals':
        return <Approvals />
      case 'goals':
        return <GoalsSetup />
      case 'performance':
        return <Performance />
      case 'billing':
        return <UsageBilling />
      default:
        return <Dashboard />
    }
  }

  return (
    <div className="authenticated-portal">
      {/* Header */}
      <header className="portal-header">
        <div className="portal-header-content">
          <div className="logo">
            <img src={logoImage} alt="WAOOAW Logo" className="logo-image" />
          </div>
          <nav className="portal-nav">
            <a href="#dashboard" className={currentPage === 'dashboard' ? 'active' : ''}>Dashboard</a>
            <a href="#agents" className={currentPage === 'my-agents' ? 'active' : ''}>My Agents</a>
            <a href="#goals" className={currentPage === 'goals' ? 'active' : ''}>Goals</a>
            <a href="#approvals" className={currentPage === 'approvals' ? 'active' : ''}>
              Approvals{pendingApprovalsCount > 0 && `(${pendingApprovalsCount})`}
            </a>
            <a href="#performance" className={currentPage === 'performance' ? 'active' : ''}>Performance</a>
            <a href="#billing" className={currentPage === 'billing' ? 'active' : ''}>Billing</a>
          </nav>
          <div className="portal-header-actions">
            <Button 
              appearance="subtle" 
              icon={theme === 'light' ? <WeatherMoon20Regular /> : <WeatherSunny20Regular />}
              onClick={toggleTheme}
              aria-label="Toggle theme"
            />
            <Button 
              appearance="subtle" 
              icon={<SignOut20Regular />}
              onClick={onLogout}
            >
              Sign Out
            </Button>
          </div>
        </div>
      </header>

      <div className="portal-layout">
        {/* Sidebar */}
        <aside className={`portal-sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
          <nav className="sidebar-nav">
            {menuItems.map(item => (
              <button
                key={item.id}
                className={`sidebar-item ${currentPage === item.id ? 'active' : ''}`}
                onClick={() => setCurrentPage(item.id)}
              >
                <span className="sidebar-icon">{item.icon}</span>
                {!sidebarCollapsed && (
                  <>
                    <span className="sidebar-label">{item.label}</span>
                    {item.badge && <span className="sidebar-badge">{item.badge}</span>}
                  </>
                )}
              </button>
            ))}
          </nav>
          <div className="sidebar-footer">
            <button 
              className="sidebar-toggle"
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {sidebarCollapsed ? '→' : '←'}
            </button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="portal-content">
          {renderPage()}
        </main>
      </div>
    </div>
  )
}
