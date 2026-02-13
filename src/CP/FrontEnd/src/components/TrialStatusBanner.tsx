import {
  MessageBar,
  MessageBarBody,
  MessageBarTitle,
  Button,
  makeStyles,
  shorthands,
  tokens
} from '@fluentui/react-components'
import { Warning24Filled, Clock24Regular } from '@fluentui/react-icons'
import { useNavigate } from 'react-router-dom'

const useStyles = makeStyles({
  banner: {
    marginBottom: tokens.spacingVerticalL,
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
  },
  actions: {
    display: 'flex',
    ...shorthands.gap(tokens.spacingHorizontalS),
    marginTop: tokens.spacingVerticalS,
    flexWrap: 'wrap'
  }
})

interface TrialStatusBannerProps {
  agentNickname: string
  daysRemaining: number
  subscriptionId: string
  onUpgrade?: () => void
  onDismiss?: () => void
}

/**
 * Prominent banner showing trial expiration warning with upgrade CTA
 * Display rules:
 * - Show when daysRemaining <= 3
 * - Warning intent when daysRemaining <= 1
 * - Info intent when 2-3 days remain
 */
export function TrialStatusBanner({ 
  agentNickname, 
  daysRemaining, 
  subscriptionId,
  onUpgrade,
  onDismiss 
}: TrialStatusBannerProps) {
  const styles = useStyles()
  const navigate = useNavigate()

  // Don't show if more than 3 days remain
  if (daysRemaining > 3) return null

  const intent = daysRemaining <= 1 ? 'warning' : 'info'
  const icon = daysRemaining <= 1 ? <Warning24Filled /> : <Clock24Regular />
  
  const title = daysRemaining === 0 
    ? 'Trial Expires Today!' 
    : `Trial Expires in ${daysRemaining} Day${daysRemaining !== 1 ? 's' : ''}`

  const message = daysRemaining === 0
    ? `Your trial for "${agentNickname}" expires today. Keep deliverables by upgrading now or they'll be archived.`
    : `Your trial for "${agentNickname}" is ending soon. Keep your agent and all deliverables by upgrading to paid.`

  const handleUpgrade = () => {
    if (onUpgrade) {
      onUpgrade()
    } else {
      // Navigate to trial dashboard with conversion flow
      navigate(`/portal/billing?upgrade=${subscriptionId}`)
    }
  }

  return (
    <MessageBar
      intent={intent}
      className={styles.banner}
      icon={icon}
    >
      <MessageBarBody>
        <MessageBarTitle>{title}</MessageBarTitle>
        <div>{message}</div>
        <div className={styles.actions}>
          <Button 
            appearance={intent === 'warning' ? 'primary' : 'secondary'}
            size="small"
            onClick={handleUpgrade}
          >
            Upgrade to Paid (₹12k/mo)
          </Button>
          <Button 
            appearance="transparent"
            size="small"
            onClick={() => navigate('/portal/trials')}
          >
            View All Trials
          </Button>
          {onDismiss && (
            <Button 
              appearance="transparent"
              size="small"
              onClick={onDismiss}
            >
              Dismiss
            </Button>
          )}
        </div>
      </MessageBarBody>
    </MessageBar>
  )
}

interface TrialStatusIndicatorProps {
  daysRemaining: number
  inline?: boolean
}

/**
 * Inline trial status indicator with days remaining
 * Shows color-coded badge based on urgency
 */
export function TrialStatusIndicator({ daysRemaining, inline = false }: TrialStatusIndicatorProps) {
  const getColor = () => {
    if (daysRemaining <= 1) return tokens.colorPaletteRedForeground1
    if (daysRemaining <= 3) return tokens.colorPaletteYellowForeground1
    return tokens.colorPaletteGreenForeground1
  }

  const getIcon = () => {
    if (daysRemaining <= 1) return <Warning24Filled style={{ fontSize: '16px' }} />
    return <Clock24Regular style={{ fontSize: '16px' }} />
  }

  const style: React.CSSProperties = inline 
    ? {
        display: 'inline-flex',
        alignItems: 'center',
        gap: tokens.spacingHorizontalXS,
        color: getColor(),
        fontWeight: tokens.fontWeightSemibold,
        fontSize: tokens.fontSizeBase200
      }
    : {
        display: 'flex',
        alignItems: 'center',
        gap: tokens.spacingHorizontalXS,
        padding: `${tokens.spacingVerticalXS} ${tokens.spacingHorizontalS}`,
        borderRadius: tokens.borderRadiusMedium,
        backgroundColor: tokens.colorNeutralBackground2,
        color: getColor(),
        fontWeight: tokens.fontWeightSemibold,
        fontSize: tokens.fontSizeBase200,
        border: `1px solid ${getColor()}`
      }

  return (
    <div style={style}>
      {getIcon()}
      <span>{daysRemaining === 0 ? 'Expires today' : `${daysRemaining}d left`}</span>
    </div>
  )
}
