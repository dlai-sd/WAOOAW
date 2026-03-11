import { Badge, Card } from '@fluentui/react-components'

import type { GoalSchemaField } from '../services/agentSkills.service'

interface DigitalMarketingBriefSummaryCardProps {
  title?: string
  subtitle?: string
  fields: GoalSchemaField[]
  values: Record<string, unknown>
  emptyMessage?: string
  compact?: boolean
}

function hasValue(value: unknown): boolean {
  if (Array.isArray(value)) return value.length > 0
  if (value && typeof value === 'object') return Object.keys(value as Record<string, unknown>).length > 0
  return String(value ?? '').trim().length > 0
}

function formatValue(value: unknown): string {
  if (Array.isArray(value)) return value.join(', ')
  if (value && typeof value === 'object') {
    try {
      return JSON.stringify(value)
    } catch {
      return 'Structured response captured'
    }
  }
  return String(value ?? '').trim()
}

export function DigitalMarketingBriefSummaryCard({
  title = 'Brief summary',
  subtitle = 'Review what the agent will use to generate drafts and publishing decisions.',
  fields,
  values,
  emptyMessage = 'Start answering the conversation prompts and the structured brief will appear here.',
  compact = false,
}: DigitalMarketingBriefSummaryCardProps) {
  const completedRequired = fields.filter((field) => field.required && hasValue(values[field.key])).length
  const totalRequired = fields.filter((field) => field.required).length
  const filledFields = fields.filter((field) => hasValue(values[field.key]))

  return (
    <Card
      style={{
        padding: compact ? '1rem' : '1.25rem',
        display: 'flex',
        flexDirection: 'column',
        gap: compact ? '0.75rem' : '1rem',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.5rem', flexWrap: 'wrap' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: compact ? '1rem' : '1.1rem' }}>{title}</h3>
            <div style={{ marginTop: '0.3rem', opacity: 0.78, fontSize: compact ? '0.85rem' : '0.9rem' }}>
              {subtitle}
            </div>
          </div>
          <Badge appearance="tint" color={completedRequired === totalRequired && totalRequired > 0 ? 'success' : 'informative'}>
            {completedRequired}/{totalRequired || fields.length} core details
          </Badge>
        </div>
      </div>

      {filledFields.length === 0 ? (
        <div
          style={{
            borderRadius: '12px',
            border: '1px dashed var(--colorNeutralStroke2)',
            padding: compact ? '0.85rem' : '1rem',
            opacity: 0.8,
            lineHeight: 1.5,
          }}
        >
          {emptyMessage}
        </div>
      ) : (
        <div style={{ display: 'grid', gap: compact ? '0.6rem' : '0.75rem' }}>
          {fields.map((field) => {
            if (!hasValue(values[field.key])) return null

            return (
              <div
                key={field.key}
                style={{
                  borderRadius: '12px',
                  border: '1px solid var(--colorNeutralStroke2)',
                  padding: compact ? '0.75rem 0.85rem' : '0.85rem 1rem',
                }}
              >
                <div style={{ fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.06em', opacity: 0.68 }}>
                  {field.label}
                </div>
                <div style={{ marginTop: '0.3rem', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>
                  {formatValue(values[field.key])}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </Card>
  )
}

export default DigitalMarketingBriefSummaryCard