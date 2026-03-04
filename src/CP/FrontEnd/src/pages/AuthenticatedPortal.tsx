import { useState } from 'react'
import { Button } from '@fluentui/react-components'
import { 
  WeatherMoon20Regular, 
  WeatherSunny20Regular,
  Home20Regular,
  Bot20Regular,
  Target20Regular,
  Payment20Regular,
  Settings20Regular,
  SignOut20Regular,
  Search20Regular,
  DocumentBulletList20Regular,
  Mail20Regular,
} from '@fluentui/react-icons'
import logoImage from '../Waooaw-Logo.png'
import AgentDiscovery from './AgentDiscovery'
import AgentDetail from './AgentDetail'
import CommandCentre from './authenticated/CommandCentre'
import MyAgents from './authenticated/MyAgents'
import GoalsSetup from './authenticated/GoalsSetup'
import Deliverables from './authenticated/Deliverables'
import Inbox from './authenticated/Inbox'
import UsageBilling from './authenticated/UsageBilling'
import ProfileSettings from './authenticated/ProfileSettings'

interface AuthenticatedPortalProps {
  theme: 'light' | 'dark'
  toggleTheme: () => void
  onLogout: () => void
  initialPage?: Page
  initialAgentId?: string
}

type Page = 'command-centre' | 'my-agents' | 'goals' | 'deliverables' | 'inbox' | 'billing' | 'profile-settings' | 'discover' | 'agent-detail'

export default function AuthenticatedPortal({ theme, toggleTheme, onLogout, initialPage, initialAgentId }: AuthenticatedPortalProps) {
  const [currentPage, setCurrentPage] = useState<Page>(initialPage ?? 'command-centre')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [selectedAgentId, setSelectedAgentId] = useState<string | undefined>(initialAgentId)

  const handleSelectAgent = (agentId: string) => {
    setSelectedAgentId(agentId)
    setCurrentPage('agent-detail')
  }

  const handleBackToDiscovery = () => {
    setSelectedAgentId(undefined)
    setCurrentPage('discover')
  }

  // agent-detail is a sub-page of discover — keep Discover highlighted in sidebar
  const activeNavPage: Page = currentPage === 'agent-detail' ? 'discover' : currentPage

  const inboxCount = 1 // Mock unread count

  const menuItems: Array<{ id: Page; icon: React.ReactNode; label: string; badge?: number }> = [
    { id: 'command-centre', icon: <Home20Regular />, label: 'Command Centre' },
    { id: 'my-agents', icon: <Bot20Regular />, label: 'My Agents' },
    { id: 'discover', icon: <Search20Regular />, label: 'Discover' },
    { id: 'goals', icon: <Target20Regular />, label: 'Goals' },
    { id: 'deliverables', icon: <DocumentBulletList20Regular />, label: 'Deliverables' },
    { id: 'inbox', icon: <Mail20Regular />, label: 'Inbox', badge: inboxCount },
    { id: 'billing', icon: <Payment20Regular />, label: 'Subscriptions & Billing' },
    { id: 'profile-settings', icon: <Settings20Regular />, label: 'Profile & Settings' },
  ]

  const renderPage = () => {
    switch (currentPage) {
      case 'command-centre':
        return <CommandCentre />
      case 'my-agents':
        return <MyAgents onNavigateToDiscover={() => setCurrentPage('discover')} />
      case 'discover':
        return <AgentDiscovery onSelectAgent={handleSelectAgent} />
      case 'agent-detail':
        return <AgentDetail agentIdProp={selectedAgentId} onBack={handleBackToDiscovery} />
      case 'goals':
        return <GoalsSetup />
      case 'deliverables':
        return <Deliverables />
      case 'inbox':
        return <Inbox />
      case 'billing':
        return <UsageBilling />
      case 'profile-settings':
        return <ProfileSettings />
      default:
        return <CommandCentre />
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
                className={`sidebar-item ${activeNavPage === item.id ? 'active' : ''}`}
                onClick={() => setCurrentPage(item.id)}
              >
                <span className="sidebar-icon">{item.icon}</span>
                {!sidebarCollapsed && (
                  <>
                    <span className="sidebar-label">{item.label}</span>
                    {item.badge ? <span className="sidebar-badge">{item.badge}</span> : null}
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
