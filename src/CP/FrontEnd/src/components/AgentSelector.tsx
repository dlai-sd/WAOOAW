import { 
  Dropdown, 
  Option, 
  Badge,
  Spinner,
  makeStyles,
  shorthands,
  tokens
} from '@fluentui/react-components'
import { 
  Bot24Regular,
  CheckmarkCircle20Filled,
  Warning20Filled,
  Clock20Regular
} from '@fluentui/react-icons'

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap(tokens.spacingVerticalS),
    width: '100%',
    maxWidth: '480px'
  },
  label: {
    fontWeight: tokens.fontWeightSemibold,
    fontSize: tokens.fontSizeBase300,
    color: tokens.colorNeutralForeground1
  },
  dropdown: {
    minWidth: '320px',
    width: '100%'
  },
  optionContent: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap(tokens.spacingHorizontalS),
    width: '100%'
  },
  optionIcon: {
    color: tokens.colorBrandForeground1,
    fontSize: '20px',
    flexShrink: 0
  },
  optionText: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('2px'),
    flex: 1,
    minWidth: 0
  },
  optionPrimary: {
    fontWeight: tokens.fontWeightSemibold,
    color: tokens.colorNeutralForeground1,
    ...shorthands.overflow('hidden'),
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap'
  },
  optionSecondary: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
    ...shorthands.overflow('hidden'),
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap'
  },
  optionBadges: {
    display: 'flex',
    ...shorthands.gap(tokens.spacingHorizontalXS),
    flexShrink: 0,
    alignItems: 'center'
  },
  loading: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap(tokens.spacingHorizontalS),
    ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
    color: tokens.colorNeutralForeground2
  },
  empty: {
    ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
    color: tokens.colorNeutralForeground3,
    fontStyle: 'italic'
  },
  helperText: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
    marginTop: tokens.spacingVerticalXS
  }
})

export interface AgentInstance {
  subscription_id: string
  nickname?: string | null
  agent_id: string
  agent_type_id?: string | null
  status: string
  trial_status?: string | null
  trial_end_at?: string | null
  configured?: boolean
}

interface AgentSelectorProps {
  agents: AgentInstance[]
  selectedId: string
  onChange: (subscriptionId: string) => void
  loading?: boolean
  disabled?: boolean
  label?: string
  helperText?: string
  required?: boolean
}

function getAgentTypeFriendlyName(agentTypeId?: string | null): string {
  if (!agentTypeId) return 'Agent'
  if (agentTypeId.startsWith('trading.')) return 'Trading Agent'
  if (agentTypeId.startsWith('marketing.')) return 'Marketing Agent'
  return 'Agent'
}

function getStatusIcon(agent: AgentInstance) {
  const status = String(agent.status || 'active').toLowerCase()
  const trialStatus = String(agent.trial_status || '').toLowerCase()
  
  if (status === 'canceled') {
    return <Warning20Filled style={{ color: tokens.colorPaletteRedForeground1 }} />
  }
  
  if (trialStatus === 'active' && agent.trial_end_at) {
    return <Clock20Regular style={{ color: tokens.colorPaletteYellowForeground1 }} />
  }
  
  if (agent.configured) {
    return <CheckmarkCircle20Filled style={{ color: tokens.colorPaletteGreenForeground1 }} />
  }
  
  return <Bot24Regular style={{ color: tokens.colorBrandForeground1 }} />
}

function getStatusBadge(agent: AgentInstance) {
  const status = String(agent.status || 'active').toLowerCase()
  const trialStatus = String(agent.trial_status || '').toLowerCase()
  
  if (status === 'canceled') {
    return <Badge appearance="ghost" color="danger" size="small">Ended</Badge>
  }
  
  if (trialStatus === 'active' && agent.trial_end_at) {
    const daysRemaining = Math.ceil(
      (new Date(agent.trial_end_at).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
    )
    return (
      <Badge appearance="tint" color="warning" size="small">
        Trial ({daysRemaining}d left)
      </Badge>
    )
  }
  
  if (!agent.configured) {
    return <Badge appearance="outline" size="small">Setup Needed</Badge>
  }
  
  return <Badge appearance="filled" color="success" size="small">Active</Badge>
}

export function AgentSelector({
  agents,
  selectedId,
  onChange,
  loading = false,
  disabled = false,
  label = 'Selected Agent',
  helperText,
  required = false
}: AgentSelectorProps) {
  const styles = useStyles()
  
  const selectedAgent = agents.find(a => a.subscription_id === selectedId)
  const displayText = selectedAgent 
    ? `${selectedAgent.nickname || selectedAgent.agent_id} — ${getAgentTypeFriendlyName(selectedAgent.agent_type_id)}`
    : 'Select an agent...'
  
  if (loading) {
    return (
      <div className={styles.container}>
        {label && (
          <label className={styles.label}>
            {label}{required && ' *'}
          </label>
        )}
        <div className={styles.loading}>
          <Spinner size="tiny" />
          <span>Loading agents...</span>
        </div>
      </div>
    )
  }
  
  if (agents.length === 0) {
    return (
      <div className={styles.container}>
        {label && (
          <label className={styles.label}>
            {label}{required && ' *'}
          </label>
        )}
        <div className={styles.empty}>
          No agents hired yet
        </div>
      </div>
    )
  }
  
  return (
    <div className={styles.container}>
      {label && (
        <label className={styles.label}>
          {label}{required && ' *'}
        </label>
      )}
      
      <Dropdown
        className={styles.dropdown}
        value={displayText}
        selectedOptions={[selectedId]}
        onOptionSelect={(_, data) => {
          if (data.optionValue) {
            onChange(data.optionValue)
          }
        }}
        disabled={disabled}
        placeholder="Select an agent..."
        appearance="filled-darker"
      >
        {agents.map((agent) => {
          const typeName = getAgentTypeFriendlyName(agent.agent_type_id)
          const displayName = agent.nickname || agent.agent_id
          
          return (
            <Option
              key={agent.subscription_id}
              value={agent.subscription_id}
              text={`${displayName} — ${typeName}`}
            >
              <div className={styles.optionContent}>
                <div className={styles.optionIcon}>
                  {getStatusIcon(agent)}
                </div>
                <div className={styles.optionText}>
                  <div className={styles.optionPrimary}>
                    {displayName}
                  </div>
                  <div className={styles.optionSecondary}>
                    {typeName} • ID: {agent.agent_id}
                  </div>
                </div>
                <div className={styles.optionBadges}>
                  {getStatusBadge(agent)}
                </div>
              </div>
            </Option>
          )
        })}
      </Dropdown>
      
      {helperText && (
        <div className={styles.helperText}>
          {helperText }
        </div>
      )}
      
      {selectedAgent && !selectedAgent.configured && (
        <div className={styles.helperText} style={{ color: tokens.colorPaletteYellowForeground1 }}>
          ⚠️ Complete setup to activate this agent
        </div>
      )}
    </div>
  )
}
