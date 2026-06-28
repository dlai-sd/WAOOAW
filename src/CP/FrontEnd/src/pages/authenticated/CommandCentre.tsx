import { Button, Card, Spinner } from '@fluentui/react-components'
import { useEffect, useMemo, useState } from 'react'

import {
  getMyAgentsSummary,
  type MyAgentInstanceSummary,
} from '../../services/myAgentsSummary.service'
import { listHiredAgentDeliverables, type Deliverable } from '../../services/hiredAgentDeliverables.service'

function isTradingAgent(agentId?: string | null, agentTypeId?: string | null): boolean {
  const id = String(agentId || '').trim().toUpperCase()
  const type = String(agentTypeId || '').trim().toLowerCase()
  return id.startsWith('AGT-TRD-') || type.startsWith('trading.') || type.startsWith('exchange.')
}

interface CommandCentreProps {
  onOpenDiscover: () => void
  onOpenBilling: () => void
  onOpenMyAgents: () => void
  onOpenGoals: () => void
}

export default function CommandCentre({
  onOpenDiscover,
  onOpenBilling,
  onOpenMyAgents,
  onOpenGoals,
}: CommandCentreProps) {
  const [instances, setInstances] = useState<MyAgentInstanceSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pendingTradeApprovals, setPendingTradeApprovals] = useState(0)

  useEffect(() => {
    let cancelled = false

    getMyAgentsSummary()
      .then((response) => {
        if (!cancelled) {
          setInstances(response?.instances || [])
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError('Failed to load dashboard data.')
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    const tradingInstances = instances.filter((x) => isTradingAgent(x.agent_id, x.agent_type_id) && x.hired_instance_id)
    if (tradingInstances.length === 0) {
      setPendingTradeApprovals(0)
      return
    }
    Promise.all(
      tradingInstances.map((x) =>
        listHiredAgentDeliverables(String(x.hired_instance_id)).catch(() => ({ deliverables: [] as Deliverable[] }))
      )
    ).then((results) => {
      if (cancelled) return
      const count = results.reduce(
        (acc, r) => acc + (r.deliverables ?? []).filter((d) => d.review_status === 'pending_review').length,
        0
      )
      setPendingTradeApprovals(count)
    })
    return () => {
      cancelled = true
    }
  }, [instances])

  const totalAgents = instances.length
  const inTrial = instances.filter((instance) => instance.trial_status === 'active').length
  const needsSetup = instances.filter((instance) => !instance.configured || !instance.goals_completed).length
  const configured = instances.filter((instance) => instance.configured).length

  const readinessCards = useMemo(
    () => [
      { label: 'Total agents', sublabel: 'Hired agents in your workspace', value: String(totalAgents), onClick: undefined as (() => void) | undefined },
      { label: 'In trial', sublabel: 'Agents in their 7-day trial period', value: String(inTrial), onClick: undefined },
      { label: 'Need setup', sublabel: 'Agents waiting for configuration', value: String(needsSetup), onClick: undefined },
      { label: 'Configured', sublabel: 'Agents ready and producing output', value: String(configured), onClick: undefined },
      {
        label: 'Pending trade approvals',
        sublabel: 'Trade signals waiting for your review',
        value: String(pendingTradeApprovals),
        highlight: pendingTradeApprovals > 0,
        onClick: pendingTradeApprovals > 0 ? () => {
          instances
            .filter((x) => isTradingAgent(x.agent_id, x.agent_type_id) && x.hired_instance_id)
            .forEach((x) => {
              sessionStorage.setItem(`cp_trading_active_tab_${x.hired_instance_id}`, 'approvals')
            })
          onOpenMyAgents()
        } : undefined,
      },
    ],
    [configured, inTrial, instances, needsSetup, onOpenMyAgents, pendingTradeApprovals, totalAgents]
  )

  const priorities = useMemo(() => {
    const next: string[] = []

    if (needsSetup > 0) {
      next.push(
        `${needsSetup} agent${needsSetup > 1 ? 's' : ''} need${needsSetup === 1 ? 's' : ''} setup — open My Agents to configure.`
      )
    }
    if (inTrial > 0) {
      next.push(
        `${inTrial} agent${inTrial > 1 ? 's' : ''} in trial — review output before trial ends.`
      )
    }
    if (totalAgents === 0) {
      next.push('Hire your first agent from Discover to get started.')
    }
    if (prioritiesAreClear(totalAgents, needsSetup, inTrial)) {
      next.push('All agents are set up and running. Check Deliverables for latest output.')
    }

    return next
  }, [inTrial, needsSetup, totalAgents])

  if (loading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <Spinner label="Loading dashboard data..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="dashboard-page">
        <div className="error-banner" style={{ padding: '1rem', color: '#ef4444' }}>
          {error}
        </div>
      </div>
    )
  }

  return (
    <div className="dashboard-page">
      <div className="dashboard-stats">
        {readinessCards.map((stat) => (
          <Card
            key={stat.label}
            className="stat-card"
            onClick={stat.onClick}
            style={stat.onClick ? { cursor: 'pointer' } : undefined}
          >
            <div
              className="stat-icon"
              style={'highlight' in stat && stat.highlight ? { color: '#ef4444' } : undefined}
            >
              {stat.value}
            </div>
            <div className="stat-label">{stat.label}</div>
            <div className="stat-sublabel">{stat.sublabel}</div>
          </Card>
        ))}
      </div>

      <div className="command-centre-grid">
        <Card className="command-centre-panel">
          <div className="section-header">
            <h2>Today&#39;s Flight Plan</h2>
            <span className="live-indicator">Top priorities</span>
          </div>
          <div className="command-centre-checklist">
            {priorities.map((item) => (
              <div key={item} className="command-centre-checklist-item">
                <span>•</span>
                <span>{item}</span>
              </div>
            ))}
          </div>
          <div className="command-centre-actions">
            <Button appearance="primary" onClick={onOpenMyAgents}>Open My Agents</Button>
            <Button appearance="secondary" onClick={onOpenBilling}>Review Spend</Button>
          </div>
        </Card>

        <Card className="command-centre-panel command-centre-panel--accent">
          <div className="section-header">
            <h2>Workspace Overview</h2>
            <span className="live-indicator">Current status</span>
          </div>
          <div className="command-centre-pulse-grid">
            <div>
              <div className="command-centre-pulse-value">{needsSetup}</div>
              <div className="command-centre-pulse-label">Agents needing setup</div>
            </div>
            <div>
              <div className="command-centre-pulse-value">{inTrial}</div>
              <div className="command-centre-pulse-label">Trials to review</div>
            </div>
            <div>
              <div className="command-centre-pulse-value">{priorities.length}</div>
              <div className="command-centre-pulse-label">Suggested next actions</div>
            </div>
          </div>
          <p className="command-centre-pulse-body">
            Use My Agents, Billing, and Profile to review the latest details for your account.
          </p>
        </Card>
      </div>

      <section className="activity-section">
        <div className="section-header">
          <h2>Agent Activity Feed</h2>
          <span className="live-indicator">Updates when activity is available</span>
        </div>
        <div className="activity-feed">
          <Card className="activity-card">
            <div className="activity-agent">
              {totalAgents === 0 ? 'No hired agents yet' : 'Live activity summary'}
            </div>
            <div className="activity-action">
              {totalAgents === 0
                ? 'Hire your first agent from Discover to start seeing output and approvals here.'
                : needsSetup > 0
                  ? 'Some agents still need setup before they can start delivering output.'
                  : inTrial > 0
                    ? 'Your trial agents are producing output — review Deliverables and decide what to keep.'
                    : 'Your configured agents are running. Check Deliverables for the latest work.'}
            </div>
            <div className="activity-meta">
              {totalAgents === 0
                ? 'What to do next: browse Discover and hire the first agent that matches your workflow.'
                : `Configured agents: ${configured} · Agents needing setup: ${needsSetup} · Trials active: ${inTrial}`}
            </div>
          </Card>
        </div>
      </section>

      <section className="quick-actions">
        <h2>Quick Actions</h2>
        <div className="action-grid">
          <Card className="action-card" onClick={onOpenGoals}>
            <h3>🎯 Add New Goal</h3>
            <p>Configure goals for your agents</p>
          </Card>
          <Card className="action-card" onClick={onOpenDiscover}>
            <h3>🤖 Hire Another Agent</h3>
            <p>Browse the marketplace with outcomes first</p>
          </Card>
          <Card className="action-card" onClick={onOpenBilling}>
            <h3>💰 Review Spend</h3>
            <p>Understand billing, receipts, and what changed</p>
          </Card>
        </div>
      </section>
    </div>
  )
}

function prioritiesAreClear(totalAgents: number, needsSetup: number, inTrial: number): boolean {
  return totalAgents > 0 && needsSetup === 0 && inTrial === 0
}
