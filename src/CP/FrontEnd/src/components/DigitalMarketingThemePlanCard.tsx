import { Button, Input, Textarea } from '@fluentui/react-components'

import type { DigitalMarketingDerivedTheme } from '../services/digitalMarketingActivation.service'

export function DigitalMarketingThemePlanCard(props: {
  masterTheme: string
  derivedThemes: DigitalMarketingDerivedTheme[]
  editable?: boolean
  saving?: boolean
  onMasterThemeChange?: (value: string) => void
  onSave?: () => void
}) {
  const {
    masterTheme,
    derivedThemes,
    editable = false,
    saving = false,
    onMasterThemeChange,
    onSave,
  } = props

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      <div>
        <div style={{ fontWeight: 600, marginBottom: '0.35rem' }}>Master theme</div>
        {editable ? (
          <Input
            aria-label="Master theme"
            value={masterTheme}
            onChange={(_, data) => onMasterThemeChange?.(String(data.value || ''))}
          />
        ) : (
          <div>{masterTheme || 'No master theme saved yet.'}</div>
        )}
      </div>

      <div>
        <div style={{ fontWeight: 600, marginBottom: '0.35rem' }}>Derived themes</div>
        {derivedThemes.length === 0 ? (
          <div style={{ opacity: 0.8 }}>No derived themes yet.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {derivedThemes.map((theme, index) => (
              <div key={`${theme.title}-${index}`} style={{ padding: '0.75rem', borderRadius: '10px', border: '1px solid var(--colorNeutralStroke2)' }}>
                <div style={{ fontWeight: 600 }}>{theme.title}</div>
                <div style={{ opacity: 0.85 }}>{theme.description || 'No description provided.'}</div>
                {theme.frequency ? <div style={{ marginTop: '0.25rem', opacity: 0.75 }}>Frequency: {theme.frequency}</div> : null}
              </div>
            ))}
          </div>
        )}
      </div>

      {editable ? (
        <div>
          <div style={{ fontWeight: 600, marginBottom: '0.35rem' }}>Revision notes</div>
          <Textarea
            aria-label="Theme plan revision notes"
            value={derivedThemes.map((theme) => `${theme.title}: ${theme.description || ''}`).join('\n')}
            readOnly
          />
        </div>
      ) : null}

      {editable && onSave ? (
        <div>
          <Button appearance="primary" onClick={onSave} disabled={saving || !masterTheme.trim()}>
            {saving ? 'Saving…' : 'Save theme plan'}
          </Button>
        </div>
      ) : null}
    </div>
  )
}
