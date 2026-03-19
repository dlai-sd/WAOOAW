import { useEffect, useMemo, useState } from 'react'
import { Button } from '@fluentui/react-components'
import { useLocation } from 'react-router-dom'
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
import HireReceipt from './HireReceipt'
import HireSetupWizard from './HireSetupWizard'
import CommandCentre from './authenticated/CommandCentre'
import MyAgents from './authenticated/MyAgents'
import GoalsSetup from './authenticated/GoalsSetup'
import Deliverables from './authenticated/Deliverables'
import Inbox, { type CustomerInboxItem } from './authenticated/Inbox'
import UsageBilling from './authenticated/UsageBilling'
import ProfileSettings from './authenticated/ProfileSettings'
import { getMyAgentsSummary, type MyAgentInstanceSummary } from '../services/myAgentsSummary.service'
import {
  getDeliverablePublishReadiness,
  listHiredAgentDeliverables,
  type Deliverable,
} from '../services/hiredAgentDeliverables.service'
import { isDigitalMarketingAgent } from '../services/agentSkills.service'
import { getPlatformConnectionSummary, listPlatformConnections, type PlatformConnection } from '../services/platformConnections.service'

interface AuthenticatedPortalProps {
  theme: 'light' | 'dark'
  toggleTheme: () => void
  showHelpBoxes: boolean
  toggleHelpBoxes: () => void
  onLogout: () => void
  initialPage?: Page
  initialAgentId?: string
  initialJourneyContext?: PortalJourneyContext
}

type Page = 'command-centre' | 'my-agents' | 'goals' | 'deliverables' | 'inbox' | 'billing' | 'profile-settings' | 'discover' | 'agent-detail' | 'hire-setup' | 'hire-receipt'

type JourneySource = 'payment-confirmed' | 'trial-activated' | 'setup-incomplete'
type StudioStep = 'identity' | 'platforms' | 'review'
type StudioFocus = 'identity' | 'youtube' | 'review'

type PortalJourneyContext = {
  source: JourneySource
  subscriptionId?: string
  lifecycleState?: string
  catalogVersion?: string
  agentName?: string
}

type PortalLocationState = {
  portalEntry?: {
    page?: Page
    agentId?: string
    subscriptionId?: string
    studioStep?: StudioStep
    studioFocus?: StudioFocus
    source?: JourneySource
    lifecycleState?: string
    catalogVersion?: string
    agentName?: string
  }
}

function formatLifecycleLabel(value?: string): string | null {
  const normalized = String(value || '').trim()
  if (!normalized) return null
  if (normalized === 'live_on_cp') return 'Live on CP'
  if (normalized === 'servicing_only') return 'Servicing only'
  if (normalized === 'retired_from_catalog') return 'Retired from catalog'
  return normalized.replace(/_/g, ' ')
}

function formatCount(count: number, singular: string, plural?: string): string {
  const label = count === 1 ? singular : plural || `${singular}s`
  return `${count} ${label}`
}

function summarizePayload(payload: Record<string, unknown>): string {
  const candidateKeys = ['summary', 'text_preview', 'preview', 'message', 'body', 'content']

  for (const key of candidateKeys) {
    const value = payload[key]
    if (typeof value === 'string' && value.trim()) {
      return value.trim().slice(0, 180)
    }
  }

  try {
    const raw = JSON.stringify(payload || {})
    return raw.length > 180 ? `${raw.slice(0, 177)}...` : raw
  } catch {
    return 'Deliverable content is available in My Agents.'
  }
}

function toInboxItem(
  instance: MyAgentInstanceSummary,
  deliverable: Deliverable,
  connections: PlatformConnection[] = []
): CustomerInboxItem | null {
  const normalizedStatus = String(deliverable.review_status || '').trim().toLowerCase()
  if (!['pending_review', 'approved', 'rejected'].includes(normalizedStatus)) {
    return null
  }

  const isMarketing = isDigitalMarketingAgent(instance.agent_id, instance.agent_type_id)
  const youtubeConnection = isMarketing ? getPlatformConnectionSummary(connections, 'youtube') : null
  const publishReadiness = isMarketing
    ? getDeliverablePublishReadiness(deliverable, {
        hasPlatformConnection: youtubeConnection?.isReady ?? null,
        platformLabel: 'YouTube',
      })
    : null

  return {
    deliverableId: deliverable.deliverable_id,
    hiredInstanceId: String(instance.hired_instance_id || '').trim(),
    agentLabel: String(instance.nickname || instance.agent_id || 'Your agent').trim(),
    title: String(deliverable.title || deliverable.deliverable_id || 'Untitled deliverable').trim(),
    preview: summarizePayload(deliverable.payload || {}),
    reviewStatus: normalizedStatus,
    approvalId: deliverable.approval_id || null,
    reviewNotes: deliverable.review_notes || null,
    createdAt: deliverable.created_at || null,
    updatedAt: deliverable.updated_at || null,
    channelStatusLabel: youtubeConnection?.label || null,
    publishReadinessLabel: publishReadiness?.label || null,
    publishReadinessGuidance: publishReadiness?.message || null,
  }
}

export default function AuthenticatedPortal({
  theme,
  toggleTheme,
  showHelpBoxes,
  toggleHelpBoxes,
  onLogout,
  initialPage,
  initialAgentId,
  initialJourneyContext,
}: AuthenticatedPortalProps) {
  const location = useLocation()
  const portalEntry = (location.state as PortalLocationState | null)?.portalEntry
  const derivedInitialPage = portalEntry?.page ?? initialPage ?? 'command-centre'
  const derivedInitialAgentId = portalEntry?.agentId ?? initialAgentId
  const derivedInitialSubscriptionId = portalEntry?.subscriptionId
  const derivedInitialStudioStep = portalEntry?.studioStep
  const derivedInitialStudioFocus = portalEntry?.studioFocus
  const derivedJourneyContext = portalEntry?.source
    ? {
        source: portalEntry.source,
        subscriptionId: portalEntry.subscriptionId,
        lifecycleState: portalEntry.lifecycleState,
        catalogVersion: portalEntry.catalogVersion,
        agentName: portalEntry.agentName,
      }
    : initialJourneyContext

  const [currentPage, setCurrentPage] = useState<Page>(derivedInitialPage)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [selectedAgentId, setSelectedAgentId] = useState<string | undefined>(derivedInitialAgentId)
  const [journeyContext, setJourneyContext] = useState<PortalJourneyContext | undefined>(derivedJourneyContext)
  const [inboxItems, setInboxItems] = useState<CustomerInboxItem[]>([])
  const [inboxLoading, setInboxLoading] = useState(false)
  const [inboxError, setInboxError] = useState<string | null>(null)

  useEffect(() => {
    setCurrentPage(derivedInitialPage)
  }, [derivedInitialPage])

  useEffect(() => {
    setSelectedAgentId(derivedInitialAgentId)
  }, [derivedInitialAgentId])

  useEffect(() => {
    setJourneyContext(derivedJourneyContext)
  }, [derivedJourneyContext])

  useEffect(() => {
    let cancelled = false

    const loadInboxItems = async () => {
      setInboxLoading(true)
      setInboxError(null)

      try {
        const summary = await getMyAgentsSummary()
        const instances = (summary?.instances || []).filter((instance) => String(instance.hired_instance_id || '').trim())

        if (!instances.length) {
          if (!cancelled) setInboxItems([])
          return
        }

        const results = await Promise.allSettled(
          instances.map(async (instance) => {
            const hiredInstanceId = String(instance.hired_instance_id || '').trim()
            const isMarketing = isDigitalMarketingAgent(instance.agent_id, instance.agent_type_id)
            const [response, connections] = await Promise.all([
              listHiredAgentDeliverables(hiredInstanceId),
              isMarketing ? listPlatformConnections(hiredInstanceId) : Promise.resolve([]),
            ])
            return {
              instance,
              deliverables: (response?.deliverables || []).slice(),
              connections,
            }
          })
        )

        if (cancelled) return

        const nextItems = results.flatMap((result) => {
          if (result.status !== 'fulfilled') return []
          return result.value.deliverables
            .map((deliverable) => toInboxItem(result.value.instance, deliverable, result.value.connections))
            .filter((item): item is CustomerInboxItem => Boolean(item))
        })

        nextItems.sort((left, right) => {
          const leftDate = new Date(left.updatedAt || left.createdAt || 0).getTime()
          const rightDate = new Date(right.updatedAt || right.createdAt || 0).getTime()
          return rightDate - leftDate
        })

        setInboxItems(nextItems)
        if (results.some((result) => result.status === 'rejected') && nextItems.length === 0) {
          setInboxError('We could not load your deliverable states just now.')
        }
      } catch (e: any) {
        if (!cancelled) {
          setInboxItems([])
          setInboxError(e?.message || 'Failed to load deliverable states')
        }
      } finally {
        if (!cancelled) setInboxLoading(false)
      }
    }

    void loadInboxItems()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (typeof window === 'undefined') return undefined

    const handleResize = () => {
      if (window.innerWidth > 1024) {
        setMobileNavOpen(false)
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const openPage = (page: Page) => {
    setMobileNavOpen(false)
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

  // agent-detail is a sub-page of discover; hire setup/receipt are sub-pages of My Agents.
  const activeNavPage: Page = currentPage === 'agent-detail'
    ? 'discover'
    : currentPage === 'hire-setup' || currentPage === 'hire-receipt'
      ? 'my-agents'
      : currentPage

  const inboxCounts = useMemo(
    () =>
      inboxItems.reduce(
        (acc, item) => {
          if (item.reviewStatus === 'approved') acc.approved += 1
          else if (item.reviewStatus === 'rejected') acc.rejected += 1
          else acc.pending += 1
          return acc
        },
        { pending: 0, approved: 0, rejected: 0 }
      ),
    [inboxItems]
  )

  const inboxCount = inboxCounts.pending

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
        { id: 'inbox', icon: <Mail20Regular />, label: 'Inbox', badge: inboxCount || undefined },
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
      metrics: [
        formatCount(inboxCounts.pending, 'deliverable awaiting your decision'),
        formatCount(inboxCounts.approved, 'approved deliverable still visible'),
        formatCount(inboxCounts.rejected, 'rejected item still tracked'),
      ],
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
  }), [inboxCounts.approved, inboxCounts.pending, inboxCounts.rejected])

  const currentMeta = pageMeta[activeNavPage]
  const journeyAgentLabel = journeyContext?.agentName || selectedAgentId || ''
  const journeyLifecycleLabel = formatLifecycleLabel(journeyContext?.lifecycleState)
  const myAgentsInitialSubscriptionId = derivedInitialSubscriptionId ?? journeyContext?.subscriptionId
  const myAgentsInitialStudioStep = derivedInitialStudioStep ?? (journeyContext?.source === 'payment-confirmed' ? 'identity' : undefined)
  const myAgentsInitialStudioFocus = derivedInitialStudioFocus ?? (journeyContext?.source === 'payment-confirmed' ? 'identity' : undefined)

  const journeyBanner = useMemo(() => {
    if (!journeyContext) return null

    const lifecycleLabel = formatLifecycleLabel(journeyContext.lifecycleState)
    const selectedLabel = journeyContext.agentName || selectedAgentId || 'your selected agent'
    const continuityNote =
      journeyContext.lifecycleState === 'servicing_only' || journeyContext.lifecycleState === 'retired_from_catalog'
        ? ' This release is no longer open for new hire, but your active hire continues under the version you already purchased.'
        : ''

    if (journeyContext.source === 'payment-confirmed') {
      return {
        eyebrow: 'Payment captured',
        title: `Setup is still required for ${selectedLabel}`,
        body: `Payment is complete, but the agent is not ready to work until setup is finished. Resume setup to connect systems and activate the trial.${continuityNote}`,
        primaryLabel: 'Open My Agents setup',
        onPrimary: () => {
          setCurrentPage('my-agents')
        },
      }
    }

    if (journeyContext.source === 'trial-activated') {
      return {
        eyebrow: 'Trial activated',
        title: `${selectedLabel} is now in runtime setup`,
        body: `You landed in My Agents because that is the first truthful place to confirm the runtime, monitor hydration, and continue operating without guessing.${continuityNote}`,
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
  }, [journeyContext, selectedAgentId])

  const renderPage = () => {
    switch (currentPage) {
      case 'command-centre':
        return <CommandCentre onOpenDiscover={() => openPage('discover')} onOpenBilling={() => openPage('billing')} onOpenMyAgents={() => openPage('my-agents')} onOpenGoals={() => openPage('goals')} />
      case 'my-agents':
        return (
          <MyAgents
            onNavigateToDiscover={() => openPage('discover')}
            initialSubscriptionId={myAgentsInitialSubscriptionId}
          />
        )
      case 'discover':
        return <AgentDiscovery onSelectAgent={handleSelectAgent} />
      case 'agent-detail':
        return <AgentDetail agentIdProp={selectedAgentId} onBack={handleBackToDiscovery} />
      case 'hire-setup':
        return <HireSetupWizard />
      case 'hire-receipt':
        return <HireReceipt />
      case 'goals':
        return <GoalsSetup />
      case 'deliverables':
        return <Deliverables />
      case 'inbox':
        return <Inbox items={inboxItems} loading={inboxLoading} error={inboxError} onOpenMyAgents={() => openPage('my-agents')} />
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
          <div className="portal-header-primary">
            <Button
              appearance="subtle"
              className="mobile-menu-toggle"
              onClick={() => setMobileNavOpen((open) => !open)}
              aria-label={mobileNavOpen ? 'Close navigation menu' : 'Open navigation menu'}
              aria-expanded={mobileNavOpen}
              data-testid="cp-portal-mobile-menu-toggle"
            >
              {mobileNavOpen ? 'Close' : 'Menu'}
            </Button>
            <div className="portal-brand-copy">
              <div className="logo">
                <img src={logoImage} alt="WAOOAW Logo" className="logo-image" />
              </div>
              <div>
                <div className="portal-brand-title">WAOOAW Customer OS</div>
                <div className="portal-brand-subtitle">Hire, approve, monitor, and scale your AI workforce</div>
              </div>
            </div>
          </div>
          <div className="portal-header-actions">
            <div className="portal-header-status">
              <div className="portal-header-chip">Customer shell</div>
              <div className="portal-header-chip portal-header-chip--success">Truthful state first</div>
            </div>
            <div className="portal-header-controls">
              <Button
                appearance="subtle"
                className="portal-help-toggle"
                onClick={toggleHelpBoxes}
                aria-label={showHelpBoxes ? 'Hide help boxes' : 'Show help boxes'}
                data-testid="cp-portal-help-toggle"
              >
                {showHelpBoxes ? 'Hide Help' : 'Show Help'}
              </Button>
              <Button
                appearance="subtle"
                className="portal-theme-toggle"
                icon={theme === 'light' ? <WeatherMoon20Regular /> : <WeatherSunny20Regular />}
                onClick={toggleTheme}
                aria-label="Toggle theme"
              />
              <Button
                appearance="subtle"
                className="portal-signout-button"
                icon={<SignOut20Regular />}
                onClick={onLogout}
                data-testid="cp-signout-button"
              >
                Sign Out
              </Button>
            </div>
          </div>
        </div>
      </header>

      {mobileNavOpen ? (
        <button
          type="button"
          className="portal-overlay"
          aria-label="Close navigation menu"
          onClick={() => setMobileNavOpen(false)}
          data-testid="cp-portal-overlay"
        />
      ) : null}

      <div className="portal-layout">
        <aside className={`portal-sidebar ${sidebarCollapsed ? 'collapsed' : ''} ${mobileNavOpen ? 'open' : ''}`}>
          <div className="portal-sidebar-card" data-help-box="true">
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
                  {journeyAgentLabel ? <span>Agent: {journeyAgentLabel}</span> : null}
                  {journeyContext?.subscriptionId ? <span>Subscription: {journeyContext.subscriptionId}</span> : null}
                  {journeyContext?.catalogVersion ? <span>Version: {journeyContext.catalogVersion}</span> : null}
                  {journeyLifecycleLabel ? <span>Lifecycle: {journeyLifecycleLabel}</span> : null}
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
