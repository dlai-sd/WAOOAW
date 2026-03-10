import { useEffect, useMemo, useState } from 'react'
import { Button } from '@fluentui/react-components'
import { useLocation, useNavigate } from 'react-router-dom'
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
  initialJourneyContext?: PortalJourneyContext
}

type Page = 'command-centre' | 'my-agents' | 'goals' | 'deliverables' | 'inbox' | 'billing' | 'profile-settings' | 'discover' | 'agent-detail'

type JourneySource = 'payment-confirmed' | 'trial-activated' | 'setup-incomplete'

type PortalJourneyContext = {
  source: JourneySource
  subscriptionId?: string
}

type PortalLocationState = {
  portalEntry?: {
    page?: Page
    agentId?: string
    source?: JourneySource
    subscriptionId?: string
  }
}

export default function AuthenticatedPortal({ theme, toggleTheme, onLogout, initialPage, initialAgentId, initialJourneyContext }: AuthenticatedPortalProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const portalEntry = (location.state as PortalLocationState | null)?.portalEntry
  const derivedInitialPage = portalEntry?.page ?? initialPage ?? 'command-centre'
  const derivedInitialAgentId = portalEntry?.agentId ?? initialAgentId
  const derivedJourneyContext = portalEntry?.source
    ? {
        source: portalEntry.source,
        subscriptionId: portalEntry.subscriptionId,
      }
    : initialJourneyContext

  const [currentPage, setCurrentPage] = useState<Page>(derivedInitialPage)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [selectedAgentId, setSelectedAgentId] = useState<string | undefined>(derivedInitialAgentId)
  const [journeyContext, setJourneyContext] = useState<PortalJourneyContext | undefined>(derivedJourneyContext)

  useEffect(() => {
    setCurrentPage(derivedInitialPage)
  }, [derivedInitialPage])

  useEffect(() => {
    setSelectedAgentId(derivedInitialAgentId)
  }, [derivedInitialAgentId])

  useEffect(() => {
    setJourneyContext(derivedJourneyContext)
  }, [derivedJourneyContext])

  const openPage = (page: Page) => {
    setJourneyContext(undefined)
    setCurrentPage(page)
  }

  const handleSelectAgent = (agentId: string) => {
    setJourneyContext(undefined)
    setSelectedAgentId(agentId)
    setCurrentPage('agent-detail')
  }

  const handleBackToDiscovery = () => {
    setJourneyContext(undefined)
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
      description: 'Use this shell to decide what to check next, not to pretend live runtime data already exists.',
      metrics: ['Open My Agents for runtime truth', 'Billing becomes real after subscriptions exist', 'Profile should reflect confirmed business data'],
    },
    'my-agents': {
      eyebrow: 'Runtime View',
      title: 'Every Hired Agent, One Clear Operating Surface',
      description: 'Track trials, active hires, deliverables, and configuration without switching mental models.',
      metrics: ['Trial and paid runtime states', 'Skill-level controls', 'Recent outputs after runtime starts'],
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
      metrics: ['Live subscription view', 'Invoice history when available', 'Receipt access after payment'],
    },
    'profile-settings': {
      eyebrow: 'Identity & Controls',
      title: 'Shape The Account Your Agents Work For',
      description: 'Keep your business profile, preferences, and team-facing details aligned with how WAOOAW operates for you.',
      metrics: ['Business identity loaded from CP', 'Only current controls shown as live', 'Support paths'],
    },
  }), [])

  const currentMeta = pageMeta[activeNavPage]

  const journeyBanner = useMemo(() => {
    if (!journeyContext) return null

    if (journeyContext.source === 'payment-confirmed') {
      return {
        eyebrow: 'Payment captured',
        title: `Setup is still required for ${selectedAgentId || 'your selected agent'}`,
        body: 'Payment is complete, but the agent is not ready to work until setup is finished. Resume setup to connect systems and activate the trial.',
        primaryLabel: 'Resume setup',
        onPrimary: () => {
          if (!journeyContext.subscriptionId || !selectedAgentId) return
          navigate(`/hire/setup/${encodeURIComponent(journeyContext.subscriptionId)}?agentId=${encodeURIComponent(selectedAgentId)}`)
        },
      }
    }

    if (journeyContext.source === 'trial-activated') {
      return {
        eyebrow: 'Trial activated',
        title: `${selectedAgentId || 'Your selected agent'} is now in runtime setup`,
        body: 'You landed in My Agents because that is the first truthful place to confirm the runtime, monitor hydration, and continue operating without guessing.',
        primaryLabel: 'Open Deliverables',
        onPrimary: () => openPage('deliverables'),
      }
    }

    return {
      eyebrow: 'Setup paused',
      title: `You still have context for ${selectedAgentId || 'this agent'}`,
      body: 'You left setup before activation. Return to the selected agent or resume setup when you are ready.',
      primaryLabel: 'Back to agent detail',
      onPrimary: () => {
        if (!selectedAgentId) {
          openPage('discover')
          return
        }
        setCurrentPage('agent-detail')
      },
    }
  }, [journeyContext, navigate, selectedAgentId])

  const renderPage = () => {
    switch (currentPage) {
      case 'command-centre':
        return <CommandCentre onOpenDiscover={() => openPage('discover')} onOpenBilling={() => openPage('billing')} onOpenMyAgents={() => openPage('my-agents')} onOpenGoals={() => openPage('goals')} />
      case 'my-agents':
        return <MyAgents onNavigateToDiscover={() => openPage('discover')} />
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
        return <CommandCentre onOpenDiscover={() => openPage('discover')} onOpenBilling={() => openPage('billing')} onOpenMyAgents={() => openPage('my-agents')} onOpenGoals={() => openPage('goals')} />
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
            <div className="portal-header-chip">Customer shell</div>
            <div className="portal-header-chip portal-header-chip--success">Truthful state first</div>
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
                <div className="portal-sidebar-card-title">Customer workspace</div>
                <div className="portal-sidebar-card-body">Use My Agents, Billing, and Profile to confirm live state. This shell avoids fake runtime counters.</div>
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
                    onClick={() => openPage(item.id)}
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

          {journeyBanner ? (
            <section className="portal-entry-banner" data-testid="cp-portal-entry-banner">
              <div>
                <div className="portal-hero-eyebrow">{journeyBanner.eyebrow}</div>
                <h2 className="portal-entry-banner-title">{journeyBanner.title}</h2>
                <p className="portal-entry-banner-body">{journeyBanner.body}</p>
                <div className="portal-entry-banner-meta">
                  {selectedAgentId ? <span>Agent: {selectedAgentId}</span> : null}
                  {journeyContext?.subscriptionId ? <span>Subscription: {journeyContext.subscriptionId}</span> : null}
                </div>
              </div>
              <div className="portal-entry-banner-actions">
                <Button appearance="primary" onClick={journeyBanner.onPrimary} data-testid="cp-portal-entry-primary">
                  {journeyBanner.primaryLabel}
                </Button>
                <Button appearance="secondary" onClick={() => setJourneyContext(undefined)}>
                  Dismiss
                </Button>
              </div>
            </section>
          ) : null}

          <div className="portal-page-shell">
            {renderPage()}
          </div>
        </main>
      </div>
    </div>
  )
}
