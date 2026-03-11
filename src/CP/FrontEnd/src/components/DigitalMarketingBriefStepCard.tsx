import { Button, Card, ProgressBar } from '@fluentui/react-components'

import { GoalFieldRenderer } from './GoalConfigForm'
import type { GoalSchemaField } from '../services/agentSkills.service'

interface DigitalMarketingBriefStepCardProps {
  title: string
  description: string
  prompt: string
  fields: GoalSchemaField[]
  values: Record<string, unknown>
  stepIndex: number
  stepCount: number
  canGoBack: boolean
  canContinue: boolean
  isSaving: boolean
  isLastStep: boolean
  missingFieldLabels: string[]
  onChange: (key: string, value: unknown) => void
  onBack: () => void
  onNext: () => void
  onSave: () => void
}

export function DigitalMarketingBriefStepCard({
  title,
  description,
  prompt,
  fields,
  values,
  stepIndex,
  stepCount,
  canGoBack,
  canContinue,
  isSaving,
  isLastStep,
  missingFieldLabels,
  onChange,
  onBack,
  onNext,
  onSave,
}: DigitalMarketingBriefStepCardProps) {
  const progress = stepCount > 0 ? (stepIndex + 1) / stepCount : 0

  return (
    <Card
      style={{
        padding: '1.25rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.08em', opacity: 0.7 }}>
              Theme Discovery step {stepIndex + 1} of {stepCount}
            </div>
            <h2 style={{ margin: '0.25rem 0 0', fontSize: '1.3rem' }}>{title}</h2>
          </div>
          <div style={{ minWidth: '160px', flex: '0 0 220px' }}>
            <ProgressBar value={progress} />
          </div>
        </div>
        <div style={{ opacity: 0.78 }}>{description}</div>
        <div
          style={{
            padding: '0.9rem 1rem',
            borderRadius: '14px',
            background: 'var(--colorNeutralBackground2)',
            border: '1px solid var(--colorNeutralStroke2)',
            fontSize: '0.95rem',
            lineHeight: 1.5,
          }}
        >
          {prompt}
        </div>
      </div>

      <div style={{ display: 'grid', gap: '0.9rem' }}>
        {fields.map((field) => (
          <GoalFieldRenderer
            key={field.key}
            field={field}
            value={values[field.key]}
            readOnly={false}
            onChange={onChange}
          />
        ))}
      </div>

      {missingFieldLabels.length > 0 && (
        <div
          style={{
            borderRadius: '12px',
            border: '1px solid var(--colorPaletteYellowBorder2)',
            background: 'var(--colorPaletteYellowBackground1)',
            padding: '0.85rem 1rem',
            fontSize: '0.9rem',
          }}
        >
          Add the remaining details for this step before continuing: {missingFieldLabels.join(', ')}.
        </div>
      )}

      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
        <Button appearance="secondary" onClick={onBack} disabled={!canGoBack}>
          Back
        </Button>
        {isLastStep ? (
          <Button appearance="primary" onClick={onSave} disabled={!canContinue || isSaving}>
            {isSaving ? 'Saving brief...' : 'Save Theme Discovery brief'}
          </Button>
        ) : (
          <Button appearance="primary" onClick={onNext} disabled={!canContinue}>
            Continue
          </Button>
        )}
      </div>
    </Card>
  )
}

export default DigitalMarketingBriefStepCard