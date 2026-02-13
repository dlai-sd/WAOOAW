import {
  MessageBar,
  MessageBarBody,
  MessageBarTitle,
  Button,
  Spinner,
  makeStyles,
  shorthands,
  tokens
} from '@fluentui/react-components'
import {
  CheckmarkCircle24Filled,
  DismissCircle24Filled,
  Warning24Filled,
  Info24Filled,
  Dismiss24Regular
} from '@fluentui/react-icons'
import { useState, useEffect } from 'react'

const useStyles = makeStyles({
  messageBar: {
    marginBottom: tokens.spacingVerticalM,
    minWidth: '300px'
  },
  loadingContainer: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap(tokens.spacingHorizontalM),
    ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    backgroundColor: tokens.colorNeutralBackground2,
    ...shorthands.border('1px', 'solid', tokens.colorNeutralStroke2)
  },
  loadingText: {
    color: tokens.colorNeutralForeground1,
    fontWeight: tokens.fontWeightSemibold
  },
  inlineSuccess: {
    display: 'inline-flex',
    alignItems: 'center',
    ...shorthands.gap(tokens.spacingHorizontalXS),
    color: tokens.colorPaletteGreenForeground1,
    fontWeight: tokens.fontWeightSemibold,
    fontSize: tokens.fontSizeBase300
  }
})

type FeedbackIntent = 'success' | 'error' | 'warning' | 'info'

interface FeedbackMessageProps {
  intent: FeedbackIntent
  title?: string
  message: string
  action?: {
    label: string
    onClick: () => void
  }
  onDismiss?: () => void
  autoDismiss?: boolean
  dismissAfter?: number
}

export function FeedbackMessage({
  intent,
  title,
  message,
  action,
  onDismiss,
  autoDismiss = false,
  dismissAfter = 5000
}: FeedbackMessageProps) {
  const styles = useStyles()
  const [visible, setVisible] = useState(true)
  
  useEffect(() => {
    if (autoDismiss && visible) {
      const timer = setTimeout(() => {
        setVisible(false)
        onDismiss?.()
      }, dismissAfter)
      return () => clearTimeout(timer)
    }
  }, [autoDismiss, dismissAfter, visible, onDismiss])
  
  if (!visible) return null
  
  return (
    <MessageBar
      intent={intent}
      className={styles.messageBar}
    >
      <MessageBarBody>
        {title && <MessageBarTitle>{title}</MessageBarTitle>}
        {message}
        {action && (
          <Button
            appearance="transparent"
            size="small"
            onClick={action.onClick}
            style={{ marginLeft: tokens.spacingHorizontalS }}
          >
            {action.label}
          </Button>
        )}
      </MessageBarBody>
      {onDismiss && (
        <Button
          appearance="transparent"
          size="small"
          icon={<Dismiss24Regular />}
          onClick={() => {
            setVisible(false)
            onDismiss()
          }}
          aria-label="Dismiss"
        />
      )}
    </MessageBar>
  )
}

interface LoadingIndicatorProps {
  message?: string
  size?: 'tiny' | 'extra-small' | 'small' | 'medium' | 'large' | 'extra-large' | 'huge'
}

export function LoadingIndicator({ message = 'Loading...', size = 'medium' }: LoadingIndicatorProps) {
  const styles = useStyles()
  
  return (
    <div className={styles.loadingContainer}>
      <Spinner size={size} />
      <span className={styles.loadingText}>{message}</span>
    </div>
  )
}

interface SuccessIndicatorProps {
  message: string
  inline?: boolean
}

export function SuccessIndicator({ message, inline = false }: SuccessIndicatorProps) {
  const styles = useStyles()
  
  if (inline) {
    return (
      <span className={styles.inlineSuccess}>
        <CheckmarkCircle24Filled />
        {message}
      </span>
    )
  }
  
  return (
    <FeedbackMessage
      intent="success"
      message={message}
      autoDismiss
      dismissAfter={3000}
    />
  )
}

interface ValidationFeedbackProps {
  field: string
  error?: string | null
  touched?: boolean
  showSuccess?: boolean
}

export function ValidationFeedback({ field, error, touched = false, showSuccess = false }: ValidationFeedbackProps) {
  if (!touched) return null
  
  if (error) {
    return (
      <div style={{ 
        color: tokens.colorPaletteRedForeground1,
        fontSize: tokens.fontSizeBase200,
        marginTop: tokens.spacingVerticalXS,
        display: 'flex',
        alignItems: 'center',
        gap: tokens.spacingHorizontalXS
      }}>
        <DismissCircle24Filled style={{ fontSize: '16px' }} />
        {error}
      </div>
    )
  }
  
  if (showSuccess) {
    return (
      <div style={{ 
        color: tokens.colorPaletteGreenForeground1,
        fontSize: tokens.fontSizeBase200,
        marginTop: tokens.spacingVerticalXS,
        display: 'flex',
        alignItems: 'center',
        gap: tokens.spacingHorizontalXS
      }}>
        <CheckmarkCircle24Filled style={{ fontSize: '16px' }} />
        Looks good!
      </div>
    )
  }
  
  return null
}

interface ProgressIndicatorProps {
  current: number
  total: number
  label?: string
  showPercentage?: boolean
}

export function ProgressIndicator({ current, total, label, showPercentage = true }: ProgressIndicatorProps) {
  const percentage = Math.round((current / total) * 100)
  
  return (
    <div style={{ 
      display: 'flex',
      flexDirection: 'column',
      gap: tokens.spacingVerticalXS,
      width: '100%'
    }}>
      {label && (
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: tokens.fontSizeBase200,
          color: tokens.colorNeutralForeground2
        }}>
          <span>{label}</span>
          {showPercentage && <span>{percentage}%</span>}
        </div>
      )}
      <div style={{
        width: '100%',
        height: '8px',
        backgroundColor: tokens.colorNeutralBackground3,
        borderRadius: tokens.borderRadiusMedium,
        overflow: 'hidden'
      }}>
        <div style={{
          width: `${percentage}%`,
          height: '100%',
          backgroundColor: tokens.colorBrandBackground,
          transition: 'width 0.3s ease',
          borderRadius: tokens.borderRadiusMedium
        }} />
      </div>
      <div style={{
        fontSize: tokens.fontSizeBase200,
        color: tokens.colorNeutralForeground3
      }}>
        {current} of {total} completed
      </div>
    </div>
  )
}

interface SaveIndicatorProps {
  status: 'idle' | 'saving' | 'saved' | 'error'
  errorMessage?: string
}

export function SaveIndicator({ status, errorMessage }: SaveIndicatorProps) {
  const styles = useStyles()
  
  if (status === 'idle') return null
  
  if (status === 'saving') {
    return (
      <div style={{ 
        display: 'inline-flex',
        alignItems: 'center',
        gap: tokens.spacingHorizontalXS,
        color: tokens.colorNeutralForeground2,
        fontSize: tokens.fontSizeBase200
      }}>
        <Spinner size="tiny" />
        Saving...
      </div>
    )
  }
  
  if (status === 'saved') {
    return (
      <div style={{ 
        display: 'inline-flex',
        alignItems: 'center',
        gap: tokens.spacingHorizontalXS,
        color: tokens.colorPaletteGreenForeground1,
        fontSize: tokens.fontSizeBase200
      }}>
        <CheckmarkCircle24Filled style={{ fontSize: '16px' }} />
        Saved
      </div>
    )
  }
  
  if (status === 'error') {
    return (
      <div style={{ 
        display: 'inline-flex',
        alignItems: 'center',
        gap: tokens.spacingHorizontalXS,
        color: tokens.colorPaletteRedForeground1,
        fontSize: tokens.fontSizeBase200
      }}>
        <DismissCircle24Filled style={{ fontSize: '16px' }} />
        {errorMessage || 'Error saving'}
      </div>
    )
  }
  
  return null
}
