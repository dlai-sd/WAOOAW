import { Button, Input, Textarea } from '@fluentui/react-components'

type DigitalMarketingDerivedTheme = {
  title: string
  description?: string
  frequency?: string
}

export function DigitalMarketingThemePlanCard(props: {
  masterTheme: string
  derivedThemes: DigitalMarketingDerivedTheme[]
  editable?: boolean
  saving?: boolean
  loading?: boolean
  error?: string | null
  onMasterThemeChange?: (value: string) => void
  onDerivedThemeChange?: (index: number, field: keyof DigitalMarketingDerivedTheme, value: string) => void
  onAddDerivedTheme?: () => void
  onGenerate?: () => void
  onRegenerate?: () => void
  onSave?: () => void
}) {
  const {
    masterTheme,
    derivedThemes,
    editable = false,
    saving = false,
    loading = false,
    error = null,
    onMasterThemeChange,
    onDerivedThemeChange,
    onAddDerivedTheme,
    onGenerate,
    onRegenerate,
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
                {editable ? (
                  <div style={{ display: 'grid', gap: '0.5rem' }}>
                    <Input
                      aria-label={`Derived theme title ${index + 1}`}
                      value={theme.title}
                      onChange={(_, data) => onDerivedThemeChange?.(index, 'title', String(data.value || ''))}
                    />
                    <Textarea
                      aria-label={`Derived theme description ${index + 1}`}
                      value={theme.description || ''}
                      onChange={(_, data) => onDerivedThemeChange?.(index, 'description', String(data.value || ''))}
                      resize="vertical"
                    />
                    <Input
                      aria-label={`Derived theme frequency ${index + 1}`}
                      value={theme.frequency || ''}
                      onChange={(_, data) => onDerivedThemeChange?.(index, 'frequency', String(data.value || ''))}
                    />
                  </div>
                ) : (
                  <>
                    <div style={{ fontWeight: 600 }}>{theme.title}</div>
                    <div style={{ opacity: 0.85 }}>{theme.description || 'No description provided.'}</div>
                    {theme.frequency ? <div style={{ marginTop: '0.25rem', opacity: 0.75 }}>Frequency: {theme.frequency}</div> : null}
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {editable && onAddDerivedTheme ? (
        <div>
          <Button appearance="secondary" onClick={onAddDerivedTheme}>
            Add derived theme
          </Button>
        </div>
      ) : null}

      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
        {onGenerate ? (
          <Button appearance="primary" onClick={onGenerate} disabled={loading || saving}>
            {loading ? 'Generating theme plan...' : 'Generate theme plan'}
          </Button>
        ) : null}
        {onRegenerate ? (
          <Button appearance="secondary" onClick={onRegenerate} disabled={loading || saving}>
            Regenerate theme plan
          </Button>
        ) : null}
        {editable && onSave ? (
          <Button appearance="primary" onClick={onSave} disabled={saving || loading || !masterTheme.trim()}>
            {saving ? 'Saving theme plan...' : 'Save theme plan'}
          </Button>
        ) : null}
        </div>

      {error ? (
        <div style={{ color: 'var(--colorPaletteRedForeground1)' }}>{error}</div>
      ) : null}
    </div>
  )
}
