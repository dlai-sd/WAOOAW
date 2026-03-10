import { useMemo, useState } from 'react'
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

  const menuSections: Array<{
    title: string
    items: Array<{ id: Page; icon: React.ReactNode; label: string; badge?: number }>
  }> = [
    {
      title: 'Operate',
      items: [
        { id: 'command-centre', icon: <Home20Regular />, label: 'Command Centre' },
        { id: 'my-agents', icon: <Bot20Regular />, label: 'My Agents' },
        { id: 'goals', icon: <Target20Regular />, label: 'Goals' },
        { id: 'deliverables', icon: <DocumentBulletList20Regular />, label: 'Deliverables' },
      ],
    },
    {
      title: 'Grow',
      items: [
        { id: 'discover', icon: <Search20Regular />, label: 'Discover' },
        { id: 'inbox', icon: <Mail20Regular />, label: 'Inbox', badge: inboxCount },
        { id: 'billing', icon: <Payment20Regular />, label: 'Subscriptions & Billing' },
        { id: 'profile-settings', icon: <Settings20Regular />, label: 'Profile & Settings' },
      ],
    },
  ]

  const pageMeta = useMemo(() => ({
    'command-centre': {
      eyebrow: 'Daily Mission',
      title: 'Run Your Agent Workforce With Confidence',
      description: 'Review what moved, what needs approval, and where spend is going before the day gets away from you.',
      metrics: ['2 active hires', '1 approval waiting', '7 goals in motion'],
    },
    'my-agents': {
      eyebrow: 'Runtime View',
      title: 'Every Hired Agent, One Clear Operating Surface',
      description: 'Track trials, active hires, deliverables, and configuration without switching mental models.',
      metrics: ['Trial + paid agents', 'Skill-level controls', 'Recent outputs'],
    },
    'discover': {
      eyebrow: 'Marketplace',
      title: 'Browse Talent, Not Generic Software',
      description: 'Find specialised agents by outcome, vertical fit, and readiness so you can hire with less guesswork.',
      metrics: ['Live marketplace', '7-day trials', 'Outcome-led profiles'],
    },
    'goals': {
      eyebrow: 'Goal Desk',
      title: 'Set Direction Without Micromanaging',
      description: 'Give your agents clear operating goals, then monitor whether the work ladder is actually moving.',
      metrics: ['Goal templates', 'Frequency controls', 'Business outcomes'],
    },
    'deliverables': {
      eyebrow: 'Work Feed',
      title: 'See What Your Agents Have Produced',
      description: 'Review drafts, outputs, and completed work in one place instead of hunting through chats and notifications.',
      metrics: ['Drafts', 'Approved work', 'Published output'],
    },
    'inbox': {
      eyebrow: 'Signal Centre',
      title: 'Keep Approvals And Requests From Falling Through',
      description: 'Prioritise the small number of decisions only you should make, then let the system move again.',
      metrics: ['Approvals', 'Status changes', 'Customer-ready updates'],
    },
    'billing': {
      eyebrow: 'Spend & Proof',
      title: 'Understand What You Are Paying For',
      description: 'Track subscriptions, invoices, receipts, and upcoming billing with less ambiguity and more trust.',
      metrics: ['Subscription view', 'Invoice history', 'Receipt access'],
    },
    'profile-settings': {
      eyebrow: 'Identity & Controls',
      title: 'Shape The Account Your Agents Work For',
      description: 'Keep your business profile, preferences, and team-facing details aligned with how WAOOAW operates for you.',
      metrics: ['Business identity', 'Preferences', 'Support paths'],
    },
  }), [])

  const currentMeta = pageMeta[activeNavPage]

  const renderPage = () => {
    switch (currentPage) {
      case 'command-centre':
        return <CommandCentre onOpenDiscover={() => setCurrentPage('discover')} onOpenBilling={() => setCurrentPage('billing')} onOpenMyAgents={() => setCurrentPage('my-agents')} />
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
    <div className="authenticated-portal" data-testid="cp-portal-root">
      {/* Header */}
      <header className="portal-header">
        <div className="portal-header-content">
          <div className="portal-brand-copy">
            <div className="logo">
              <img src={logoImage} alt="WAOOAW Logo" className="logo-image" />
            </div>
            <div>
              <div className="portal-brand-title">WAOOAW Customer OS</div>
              <div className="portal-brand-subtitle">Hire, approve, monitor, and scale your AI workforce</div>
            </div>
          </div>
          <div className="portal-header-actions">
            <div className="portal-header-chip">1 approval waiting</div>
            <div className="portal-header-chip portal-header-chip--success">Systems healthy</div>
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
              data-testid="cp-signout-button"
            >
              Sign Out
            </Button>
          </div>
        </div>
      </header>

      <div className="portal-layout">
        <aside className={`portal-sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
          <div className="portal-sidebar-card">
            <div className="portal-sidebar-card-label">Workspace</div>
            {!sidebarCollapsed && (
              <>
                <div className="portal-sidebar-card-title">GlowRevive Wellness</div>
                <div className="portal-sidebar-card-body">2 active agents · 1 decision waiting · next billing in 5 days</div>
              </>
            )}
          </div>

          <nav className="sidebar-nav">
            {menuSections.map((section) => (
              <div key={section.title} className="sidebar-section">
                {!sidebarCollapsed && <div className="sidebar-section-title">{section.title}</div>}
                {section.items.map(item => (
                  <button
                    key={item.id}
                    className={`sidebar-item ${activeNavPage === item.id ? 'active' : ''}`}
                    onClick={() => setCurrentPage(item.id)}
                    data-testid={`cp-nav-${item.id}`}
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
              </div>
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
        <main className="portal-content">
          <section className="portal-hero">
            <div>
              <div className="portal-hero-eyebrow">{currentMeta.eyebrow}</div>
              <h1 className="portal-hero-title">{currentMeta.title}</h1>
              <p className="portal-hero-description">{currentMeta.description}</p>
            </div>
            <div className="portal-hero-metrics">
              {currentMeta.metrics.map((metric) => (
                <div key={metric} className="portal-hero-metric">{metric}</div>
              ))}
            </div>
          </section>

          <div className="portal-page-shell">
            {renderPage()}
          </div>
        </main>
      </div>
    </div>
  )
}
