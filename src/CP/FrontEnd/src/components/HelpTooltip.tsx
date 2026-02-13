import {
  Tooltip as FluentTooltip,
  Button,
  makeStyles,
  shorthands,
  tokens
} from '@fluentui/react-components'
import {
  Info20Regular,
  QuestionCircle20Regular,
  Warning20Regular
} from '@fluentui/react-icons'
import { ReactNode } from 'react'

const useStyles = makeStyles({
  helpButton: {
    minWidth: 'unset',
    ...shorthands.padding('4px'),
    cursor: 'help'
  },
  tooltipContent: {
    maxWidth: '320px',
    fontSize: tokens.fontSizeBase200,
    lineHeight: '1.5'
  },
  tooltipTitle: {
    fontWeight: tokens.fontWeightSemibold,
    marginBottom: tokens.spacingVerticalXS,
    color: tokens.colorNeutralForeground1
  },
  tooltipText: {
    color: tokens.colorNeutralForeground2
  },
  tooltipExample: {
    marginTop: tokens.spacingVerticalXS,
    ...shorthands.padding(tokens.spacingVerticalXS, tokens.spacingHorizontalS),
    backgroundColor: tokens.colorNeutralBackground5,
    ...shorthands.borderRadius(tokens.borderRadiusSmall),
    fontFamily: 'monospace',
    fontSize: tokens.fontSizeBase100,
    color: tokens.colorNeutralForeground1
  },
  inlineHelp: {
    display: 'inline-flex',
    alignItems: 'center',
    verticalAlign: 'middle',
    marginLeft: tokens.spacingHorizontalXXS
  }
})

interface HelpTooltipProps {
  /** Main help text explaining the field */
  content: string
  /** Optional title for the tooltip */
  title?: string
  /** Optional code example to show */
  example?: string
  /** Icon variant: 'info' (default), 'question', 'warning' */
  variant?: 'info' | 'question' | 'warning'
  /** Display as inline (next to label) or as standalone button */
  inline?: boolean
}

/**
 * Contextual help tooltip component
 * Provides explanatory text, examples, and guidance for complex form fields
 * 
 * Usage:
 * ```tsx
 * <Label>
 *   API Key
 *   <HelpTooltip 
 *     content="Your Delta Exchange API key from Settings > API Management"
 *     example="abc123xyz456"
 *     inline
 *   />
 * </Label>
 * ```
 */
export function HelpTooltip({ 
  content, 
  title, 
  example, 
  variant = 'info',
  inline = false 
}: HelpTooltipProps) {
  const styles = useStyles()

  const getIcon = () => {
    switch (variant) {
      case 'question':
        return <QuestionCircle20Regular />
      case 'warning':
        return <Warning20Regular />
      default:
        return <Info20Regular />
    }
  }

  const getColor = () => {
    switch (variant) {
      case 'warning':
        return tokens.colorPaletteYellowForeground1
      default:
        return tokens.colorBrandForeground1
    }
  }

  const tooltipContent = (
    <div className={styles.tooltipContent}>
      {title && <div className={styles.tooltipTitle}>{title}</div>}
      <div className={styles.tooltipText}>{content}</div>
      {example && (
        <div className={styles.tooltipExample}>
          {example}
        </div>
      )}
    </div>
  )

  return (
    <FluentTooltip
      content={tooltipContent}
      relationship="description"
      positioning="above"
    >
      <Button
        appearance="transparent"
        icon={getIcon()}
        size="small"
        className={inline ? `${styles.helpButton} ${styles.inlineHelp}` : styles.helpButton}
        style={{ color: getColor() }}
        aria-label="Help"
      />
    </FluentTooltip>
  )
}

interface FieldWithHelpProps {
  /** Field label text */
  label: string
  /** Help content for tooltip */
  help: string
  /** Optional help title */
  helpTitle?: string
  /** Optional code example */
  helpExample?: string
  /** Mark as required with asterisk */
  required?: boolean
  /** Tooltip variant */
  helpVariant?: 'info' | 'question' | 'warning'
  /** The input component (Input, Select, Textarea, etc.) */
  children: ReactNode
}

/**
 * Field wrapper with integrated label and help tooltip
 * Provides consistent layout for form fields with contextual help
 * 
 * Usage:
 * ```tsx
 * <FieldWithHelp
 *   label="Max Units Per Order"
 *   required
 *   help="Maximum number of units (contracts) allowed per trade. Helps limit risk exposure."
 *   helpExample="1 (recommended for conservative risk)"
 * >
 *   <Input type="number" value={maxUnits} onChange={handleChange} />
 * </FieldWithHelp>
 * ```
 */
export function FieldWithHelp({
  label,
  help,
  helpTitle,
  helpExample,
  required = false,
  helpVariant = 'info',
  children
}: FieldWithHelpProps) {
  const styles = useStyles()

  return (
    <div style={{ marginBottom: tokens.spacingVerticalM }}>
      <label style={{ 
        display: 'flex', 
        alignItems: 'center',
        fontWeight: tokens.fontWeightSemibold,
        fontSize: tokens.fontSizeBase300,
        marginBottom: tokens.spacingVerticalXS,
        color: tokens.colorNeutralForeground1
      }}>
        {label}
        {required && <span style={{ color: tokens.colorPaletteRedForeground1, marginLeft: '4px' }}>*</span>}
        <HelpTooltip 
          content={help}
          title={helpTitle}
          example={helpExample}
          variant={helpVariant}
          inline
        />
      </label>
      {children}
    </div>
  )
}

// Pre-configured help tooltips for common fields
export const CommonHelpTooltips = {
  nickname: {
    content: "Give your agent a friendly name to easily identify it. Use something memorable like 'Sarah - Healthcare Marketing'.",
    example: "Sarah - LinkedIn Expert"
  },
  
  apiKey: {
    content: "Your API key from the platform's developer settings. Keep this secure and never share it publicly.",
    example: "sk_live_abc123xyz456..."
  },
  
  apiSecret: {
    content: "Your API secret used to sign requests. This should be kept even more secure than your API key.",
    warning: "Never commit API secrets to version control or share them in screenshots."
  },
  
  maxUnitsPerOrder: {
    content: "Maximum number of units (contracts) the agent can trade in a single order. Lower values reduce risk.",
    example: "1 (conservative), 5 (moderate), 10 (aggressive)"
  },
  
  maxNotionalInr: {
    content: "Maximum total value in INR that can be at risk in a single trade. Acts as a safety limit.",
    example: "10000 = ₹10,000 max per trade"
  },
  
  allowedCoins: {
    content: "List of cryptocurrency coins the agent is permitted to trade. One per line.",
    example: `BTC
ETH
SOL`
  },
  
  scheduleFrequency: {
    content: "How often the agent should run this goal. 'On demand' requires manual triggering.",
    example: "Daily: Runs once per day at scheduled time"
  },
  
  jsonConfig: {
    content: "Advanced configuration in JSON format. Must be valid JSON object.",
    example: `{
  "setting": "value",
  "enabled": true
}`
  },
  
  constraints: {
    content: "Additional constraints or rules for the agent to follow. Specify requirements, limitations, or preferences.",
    example: "Only post between 9 AM - 6 PM\nAvoid weekends\nMax 3 posts per day"
  }
}
