import { Card, Button, Badge } from '@fluentui/react-components'
import { Star20Filled } from '@fluentui/react-icons'

interface Agent {
  id: string
  name: string
  status: 'active' | 'working' | 'offline'
  rating: number
  industry: string
  specialty: string
  goalsComplete: number
  goalsTotal: number
}

export default function MyAgents() {
  const agents: Agent[] = [
    {
      id: '1',
      name: 'Content Marketing Agent',
      status: 'active',
      rating: 4.8,
      industry: 'Marketing',
      specialty: 'Healthcare Specialist',
      goalsComplete: 3,
      goalsTotal: 5
    },
    {
      id: '2',
      name: 'SDR Agent',
      status: 'working',
      rating: 4.9,
      industry: 'Sales',
      specialty: 'B2B SaaS Specialist',
      goalsComplete: 4,
      goalsTotal: 5
    }
  ]

  const getStatusBadge = (status: string) => {
    const statusMap = {
      active: { appearance: 'filled' as const, color: 'success' as const, label: 'Active' },
      working: { appearance: 'filled' as const, color: 'warning' as const, label: 'Working' },
      offline: { appearance: 'ghost' as const, color: undefined, label: 'Offline' }
    }
    const config = statusMap[status as keyof typeof statusMap]
    return <Badge appearance={config.appearance} color={config.color} size="small">{config.label}</Badge>
  }

  return (
    <div className="my-agents-page">
      <div className="page-header">
        <h1>My Active Agents ({agents.length})</h1>
        <Button appearance="primary">+ Hire New Agent</Button>
      </div>

      <div className="agents-list">
        {agents.map(agent => (
          <Card key={agent.id} className="agent-detail-card">
            <div className="agent-header">
              <div className="agent-title">
                <h2>{agent.name}</h2>
                {getStatusBadge(agent.status)}
              </div>
              <div className="agent-meta">
                <span className="agent-rating">
                  <Star20Filled style={{ color: '#f59e0b' }} /> {agent.rating}
                </span>
                <span> | {agent.industry} | {agent.specialty}</span>
              </div>
            </div>

            <div className="agent-goals">
              <h3>Current Goals ({agent.goalsComplete}/{agent.goalsTotal} Complete):</h3>
              <div className="goal-progress">
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${(agent.goalsComplete / agent.goalsTotal) * 100}%` }}
                  />
                </div>
                <span>{Math.round((agent.goalsComplete / agent.goalsTotal) * 100)}%</span>
              </div>
            </div>

            <div className="agent-performance">
              <h4>Performance Today:</h4>
              <ul>
                <li>Query Budget: $0.75/$1.00 (75%) 🟢</li>
                <li>Approval Response: 4.2 min avg</li>
                <li>Tasks Completed: 8</li>
              </ul>
            </div>

            <div className="agent-actions">
              <Button appearance="outline">View Dashboard</Button>
              <Button appearance="outline">Configure Goals</Button>
              <Button appearance="outline">Settings</Button>
              <Button appearance="subtle">⏸ Interrupt</Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
