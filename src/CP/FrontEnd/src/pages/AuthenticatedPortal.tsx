import { useState } from 'react'
import type { ReactNode } from 'react'
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
import { Button } from '@fluentui/react-components'
import {
  WeatherMoon20Regular,
  WeatherSunny20Regular,
  Home20Regular,
  Bot20Regular,
  Search20Regular,
  Target20Regular,
  DocumentBulletList20Regular,
  Mail20Regular,
  Payment20Regular,
  Settings20Regular,
  SignOut20Regular
} from '@fluentui/react-icons'
import logoImage from '../Waooaw-Logo.png'
import CommandCentre from './authenticated/CommandCentre'
import MyAgents from './authenticated/MyAgents'
import AgentDiscovery from './AgentDiscovery'
import GoalsSetup from './authenticated/GoalsSetup'
import Deliverables from './authenticated/Deliverables'
import Inbox from './authenticated/Inbox'
import UsageBilling from './authenticated/UsageBilling'
import ProfileSettings from './authenticated/ProfileSettings'

interface AuthenticatedPortalProps {
  theme: 'light' | 'dark'
  toggleTheme: () => void
  onLogout: () => void
}

type Page =
  | 'command-centre'
  | 'my-agents'
  | 'discover'
  | 'goals'
  | 'deliverables'
  | 'inbox'
  | 'billing'
  | 'settings'

export default function AuthenticatedPortal({ theme, toggleTheme, onLogout }: AuthenticatedPortalProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  const currentPage = (location.pathname.split('/portal/')[1]?.split('/')[0] as Page) || 'command-centre'

  const menuItems: { id: Page; icon: ReactNode; label: string }[] = [
    { id: 'command-centre', icon: <Home20Regular />, label: 'Command Centre' },
    { id: 'my-agents', icon: <Bot20Regular />, label: 'My Agents' },
    { id: 'discover', icon: <Search20Regular />, label: 'Discover' },
    { id: 'goals', icon: <Target20Regular />, label: 'Goals' },
    { id: 'deliverables', icon: <DocumentBulletList20Regular />, label: 'Deliverables' },
    { id: 'inbox', icon: <Mail20Regular />, label: 'Inbox' },
    { id: 'billing', icon: <Payment20Regular />, label: 'Subscriptions & Billing' },
    { id: 'settings', icon: <Settings20Regular />, label: 'Profile & Settings' },
  ]

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
                className={`sidebar-item ${currentPage === item.id ? 'active' : ''}`}
                onClick={() => navigate(`/portal/${item.id}`)}
                aria-label={item.label}
              >
                <span className="sidebar-icon">{item.icon}</span>
                {!sidebarCollapsed && (
                  <span className="sidebar-label">{item.label}</span>
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
          <Routes>
            <Route index element={<Navigate to="command-centre" replace />} />
            <Route path="command-centre" element={<CommandCentre />} />
            <Route path="my-agents" element={<MyAgents />} />
            <Route path="discover" element={<AgentDiscovery />} />
            <Route path="goals" element={<GoalsSetup />} />
            <Route path="deliverables" element={<Deliverables />} />
            <Route path="inbox" element={<Inbox />} />
            <Route path="billing" element={<UsageBilling />} />
            <Route path="settings" element={<ProfileSettings />} />
            <Route path="*" element={<Navigate to="command-centre" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
