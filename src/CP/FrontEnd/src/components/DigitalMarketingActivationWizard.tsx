import { Badge, Button, Checkbox, Input } from '@fluentui/react-components'
import { useEffect, useMemo, useState } from 'react'

import type { MyAgentInstanceSummary } from '../services/myAgentsSummary.service'
import {
  generateDigitalMarketingThemePlan,
  getDigitalMarketingActivationWorkspace,
  getNextPendingPlatform,
  patchDigitalMarketingActivationWorkspace,
  patchDigitalMarketingThemePlan,
  type DigitalMarketingActivationWorkspace,
} from '../services/digitalMarketingActivation.service'
import { listPlatformConnections, type PlatformConnection } from '../services/platformConnections.service'
import { FeedbackMessage, LoadingIndicator } from './FeedbackIndicators'
import { DigitalMarketingThemePlanCard } from './DigitalMarketingThemePlanCard'

const SUPPORTED_PLATFORMS = ['youtube', 'instagram', 'facebook', 'linkedin']
const MILESTONES = ['Induct Agent', 'Prepare Agent', 'Master Theme', 'Confirm Schedule'] as const

type Milestone = 'Induct Agent' | 'Prepare Agent' | 'Master Theme' | 'Confirm Schedule'

function inferMilestone(workspace: DigitalMarketingActivationWorkspace | null): Milestone {
  if (!workspace) return 'Induct Agent'
  if (!workspace.prepare_agent.selected_platforms.length) return 'Induct Agent'
  if (!workspace.prepare_agent.all_selected_platforms_completed) return 'Prepare Agent'
  if (!workspace.campaign_setup.master_theme) return 'Master Theme'
  return 'Confirm Schedule'
}

function parseCsv(value: string): string[] {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

export function DigitalMarketingActivationWizard(props: {
  selectedInstance: MyAgentInstanceSummary | null
  readOnly: boolean
  onSavedInstance?: (patch: {
    nickname?: string | null
    configured?: boolean
    goals_completed?: boolean
    hired_instance_id?: string | null
    agent_type_id?: string | null
  }) => void
}) {
  const { selectedInstance, readOnly, onSavedInstance } = props
  const hiredInstanceId = String(selectedInstance?.hired_instance_id || '').trim()

  const [workspace, setWorkspace] = useState<DigitalMarketingActivationWorkspace | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [connections, setConnections] = useState<PlatformConnection[]>([])
  const [activeMilestone, setActiveMilestone] = useState<Milestone>('Induct Agent')
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  useEffect(() => {
    if (!hiredInstanceId) {
      setWorkspace(null)
      setLoading(false)
      return
    }
    let cancelled = false
    setLoading(true)
    setError(null)

    getDigitalMarketingActivationWorkspace(hiredInstanceId)
      .then((nextWorkspace) => {
        if (cancelled) return
        setWorkspace(nextWorkspace)
        setActiveMilestone(inferMilestone(nextWorkspace))
      })
      .catch((nextError: any) => {
        if (!cancelled) setError(nextError?.message || 'Failed to load activation workspace.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [hiredInstanceId])

  useEffect(() => {
    if (!hiredInstanceId) return
    listPlatformConnections(hiredInstanceId)
      .then(setConnections)
      .catch(() => setConnections([]))
  }, [hiredInstanceId, workspace?.updated_at])

  const nextPlatform = useMemo(() => {
    if (!workspace) return null
    return getNextPendingPlatform(workspace.prepare_agent.selected_platforms, workspace.prepare_agent.platform_steps)
  }, [workspace])

  const canFinish = Boolean(workspace?.campaign_setup?.master_theme) &&
    Boolean(workspace?.campaign_setup?.schedule?.start_date) &&
    Boolean(workspace?.prepare_agent?.all_selected_platforms_completed)

  const saveWorkspacePatch = async (patch: Record<string, unknown>) => {
    if (!hiredInstanceId) return
    setSaving(true)
    setError(null)
    try {
      const nextWorkspace = await patchDigitalMarketingActivationWorkspace(hiredInstanceId, patch)
      setWorkspace(nextWorkspace)
      setActiveMilestone(inferMilestone(nextWorkspace))
      onSavedInstance?.({
        nickname: nextWorkspace.induction.nickname,
        hired_instance_id: selectedInstance?.hired_instance_id,
        agent_type_id: selectedInstance?.agent_type_id,
      })
    } catch (nextError: any) {
      setError(nextError?.message || 'Failed to save activation workspace.')
    } finally {
      setSaving(false)
    }
  }

  const selectedPlatforms = workspace?.prepare_agent.selected_platforms || []

  if (!selectedInstance) {
    return <div>Select a hired instance to start the Digital Marketing activation wizard.</div>
  }

  if (!hiredInstanceId) {
    return <div>Select a hired instance to start the Digital Marketing activation wizard.</div>
  }

  if (loading) return <LoadingIndicator message="Loading activation workspace..." size="small" />
  if (error && !workspace) return <FeedbackMessage intent="error" title="Activation unavailable" message={error} />
  if (!workspace) return null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <div>
          <div style={{ opacity: 0.75, marginBottom: '0.25rem' }}>Digital Marketing activation wizard</div>
          <div style={{ fontWeight: 700, fontSize: '1.15rem' }}>{selectedInstance.nickname || selectedInstance.agent_id}</div>
        </div>
        <Button
          appearance="outline"
          onClick={() => saveWorkspacePatch({ help_visible: !workspace.help_visible })}
          disabled={readOnly || saving}
        >
          {workspace.help_visible ? 'Hide Help' : 'Show Help'}
        </Button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '0.75rem' }}>
        {MILESTONES.map((milestone) => (
          <button
            key={milestone}
            type="button"
            onClick={() => setActiveMilestone(milestone)}
            style={{
              padding: '0.75rem',
              borderRadius: '12px',
              border: '1px solid var(--colorNeutralStroke2)',
              background: activeMilestone === milestone ? 'var(--colorNeutralBackground3)' : 'transparent',
              textAlign: 'left',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontWeight: 600 }}>{milestone}</div>
          </button>
        ))}
      </div>

      {workspace.help_visible ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '0.75rem' }}>
          <div data-testid="dma-help-panel-primary" style={{ padding: '0.75rem', border: '1px solid var(--colorPaletteRedBorder1)', borderRadius: '12px' }}>
            Complete each milestone in order so the hire becomes runtime-ready with persisted setup state.
          </div>
          <div data-testid="dma-help-panel-secondary" style={{ padding: '0.75rem', border: '1px solid var(--colorPaletteRedBorder1)', borderRadius: '12px' }}>
            Every save round-trips through CP and Plant, so refreshing the page restores the latest induction, platform, and campaign plan data.
          </div>
        </div>
      ) : null}

      {error ? <FeedbackMessage intent="error" title="Activation workspace" message={error} /> : null}
      {successMessage ? <FeedbackMessage intent="success" message={successMessage} autoDismiss dismissAfter={2500} onDismiss={() => setSuccessMessage(null)} /> : null}

      {activeMilestone === 'Induct Agent' ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <Input aria-label="Agent nickname" value={workspace.induction.nickname} onChange={(_, data) => setWorkspace({ ...workspace, induction: { ...workspace.induction, nickname: String(data.value || '') } })} disabled={readOnly} />
          <Input aria-label="Theme" value={workspace.induction.theme} onChange={(_, data) => setWorkspace({ ...workspace, induction: { ...workspace.induction, theme: String(data.value || '') } })} disabled={readOnly} />
          <Input aria-label="Primary language" value={workspace.induction.primary_language} onChange={(_, data) => setWorkspace({ ...workspace, induction: { ...workspace.induction, primary_language: String(data.value || '') } })} disabled={readOnly} />
          <Input aria-label="Timezone" value={workspace.induction.timezone} onChange={(_, data) => setWorkspace({ ...workspace, induction: { ...workspace.induction, timezone: String(data.value || '') } })} disabled={readOnly} />
          <Input aria-label="Brand name" value={workspace.induction.brand_name} onChange={(_, data) => setWorkspace({ ...workspace, induction: { ...workspace.induction, brand_name: String(data.value || '') } })} disabled={readOnly} />
          <Input aria-label="Offerings and services" value={workspace.induction.offerings_services.join(', ')} onChange={(_, data) => setWorkspace({ ...workspace, induction: { ...workspace.induction, offerings_services: parseCsv(String(data.value || '')) } })} disabled={readOnly} />
          <Input aria-label="Location" value={workspace.induction.location} onChange={(_, data) => setWorkspace({ ...workspace, induction: { ...workspace.induction, location: String(data.value || '') } })} disabled={readOnly} />
          <div>
            <div style={{ fontWeight: 600, marginBottom: '0.35rem' }}>Selected platforms</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
              {SUPPORTED_PLATFORMS.map((platform) => (
                <Checkbox
                  key={platform}
                  label={platform}
                  checked={selectedPlatforms.includes(platform)}
                  disabled={readOnly}
                  onChange={(_, data) => {
                    const nextPlatforms = data.checked
                      ? Array.from(new Set([...selectedPlatforms, platform]))
                      : selectedPlatforms.filter((item) => item !== platform)
                    setWorkspace({
                      ...workspace,
                      prepare_agent: {
                        ...workspace.prepare_agent,
                        selected_platforms: nextPlatforms,
                        platform_steps: nextPlatforms.map((key) => {
                          const existing = workspace.prepare_agent.platform_steps.find((step) => step.platform_key === key)
                          return existing || { platform_key: key, complete: false, status: 'pending' }
                        }),
                        all_selected_platforms_completed: false,
                      },
                    })
                  }}
                />
              ))}
            </div>
          </div>
          <Button
            appearance="primary"
            disabled={readOnly || saving}
            onClick={async () => {
              await saveWorkspacePatch({
                induction: workspace.induction,
                prepare_agent: {
                  selected_platforms: workspace.prepare_agent.selected_platforms,
                  platform_steps: workspace.prepare_agent.platform_steps,
                },
              })
              setSuccessMessage('Induction saved.')
            }}
          >
            {saving ? 'Saving…' : 'Save induction'}
          </Button>
        </div>
      ) : null}

      {activeMilestone === 'Prepare Agent' ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {selectedPlatforms.length === 0 ? (
            <div>No platform steps yet. Save induction with at least one platform selected first.</div>
          ) : (
            selectedPlatforms.map((platform) => {
              const complete = Boolean(workspace.prepare_agent.platform_steps.find((step) => step.platform_key === platform)?.complete)
              const connected = connections.some((connection) => String(connection.platform_key || '').trim().toLowerCase() === platform)
              return (
                <div key={platform} style={{ padding: '0.75rem', borderRadius: '12px', border: '1px solid var(--colorNeutralStroke2)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
                    <div>
                      <div style={{ fontWeight: 600 }}>{platform}</div>
                      <div style={{ opacity: 0.8 }}>
                        {complete ? 'Prepared and saved.' : nextPlatform === platform ? 'This is the next platform to prepare.' : 'Waiting for its turn.'}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                      <Badge appearance={connected ? 'filled' : 'outline'} color={connected ? 'success' : undefined}>
                        {connected ? 'Connection found' : 'No connection found'}
                      </Badge>
                      <Button
                        appearance="primary"
                        disabled={readOnly || saving}
                        onClick={async () => {
                          const nextSteps = workspace.prepare_agent.platform_steps.map((step) =>
                            step.platform_key === platform ? { ...step, complete: true, status: 'complete' } : step
                          )
                          await saveWorkspacePatch({
                            prepare_agent: {
                              selected_platforms: workspace.prepare_agent.selected_platforms,
                              platform_steps: nextSteps,
                            },
                          })
                          setSuccessMessage(`${platform} prepared.`)
                        }}
                      >
                        Mark prepared
                      </Button>
                    </div>
                  </div>
                </div>
              )
            })
          )}
        </div>
      ) : null}

      {activeMilestone === 'Master Theme' ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {!workspace.campaign_setup.master_theme ? (
            <div>
              <Button
                appearance="primary"
                disabled={readOnly || saving}
                onClick={async () => {
                  setSaving(true)
                  setError(null)
                  try {
                    const response = await generateDigitalMarketingThemePlan(hiredInstanceId, {
                      induction: workspace.induction,
                      prepare_agent: workspace.prepare_agent,
                      campaign_setup: workspace.campaign_setup,
                    })
                    setWorkspace(response.workspace)
                    setActiveMilestone('Master Theme')
                    setSuccessMessage('Theme plan generated.')
                  } catch (nextError: any) {
                    setError(nextError?.message || 'Theme plan unavailable')
                  } finally {
                    setSaving(false)
                  }
                }}
              >
                {saving ? 'Generating…' : 'Generate theme plan'}
              </Button>
            </div>
          ) : null}

          {saving && !workspace.campaign_setup.master_theme ? <LoadingIndicator message="Generating theme plan..." size="small" /> : null}
          <DigitalMarketingThemePlanCard
            masterTheme={workspace.campaign_setup.master_theme}
            derivedThemes={workspace.campaign_setup.derived_themes}
            editable
            saving={saving}
            onMasterThemeChange={(value) => setWorkspace({
              ...workspace,
              campaign_setup: { ...workspace.campaign_setup, master_theme: value },
            })}
            onSave={async () => {
              setSaving(true)
              setError(null)
              try {
                const response = await patchDigitalMarketingThemePlan(hiredInstanceId, {
                  master_theme: workspace.campaign_setup.master_theme,
                  derived_themes: workspace.campaign_setup.derived_themes,
                  schedule: workspace.campaign_setup.schedule,
                })
                setWorkspace(response.workspace)
                setSuccessMessage('Theme plan saved.')
              } catch (nextError: any) {
                setError(nextError?.message || 'Theme plan unavailable')
              } finally {
                setSaving(false)
              }
            }}
          />
        </div>
      ) : null}

      {activeMilestone === 'Confirm Schedule' ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={{ padding: '0.75rem', borderRadius: '12px', border: '1px solid var(--colorNeutralStroke2)' }}>
            <div style={{ fontWeight: 600, marginBottom: '0.5rem' }}>Final summary</div>
            <div>Platforms: {workspace.prepare_agent.selected_platforms.join(', ') || 'None selected'}</div>
            <div>Master theme: {workspace.campaign_setup.master_theme || 'Not generated yet'}</div>
            <div>Derived themes: {workspace.campaign_setup.derived_themes.map((theme) => theme.title).join(', ') || 'None yet'}</div>
            <div>Cadence: {workspace.campaign_setup.schedule.posts_per_week || 0} posts per week</div>
          </div>
          <Input
            aria-label="Start date"
            type="date"
            value={workspace.campaign_setup.schedule.start_date}
            onChange={(_, data) => setWorkspace({
              ...workspace,
              campaign_setup: {
                ...workspace.campaign_setup,
                schedule: { ...workspace.campaign_setup.schedule, start_date: String(data.value || '') },
              },
            })}
            disabled={readOnly}
          />
          <Input
            aria-label="Posts per week"
            type="number"
            value={String(workspace.campaign_setup.schedule.posts_per_week || 0)}
            onChange={(_, data) => setWorkspace({
              ...workspace,
              campaign_setup: {
                ...workspace.campaign_setup,
                schedule: { ...workspace.campaign_setup.schedule, posts_per_week: Number(data.value || 0) },
              },
            })}
            disabled={readOnly}
          />
          <Input
            aria-label="Preferred posting hours"
            value={workspace.campaign_setup.schedule.preferred_hours_utc.join(', ')}
            onChange={(_, data) => setWorkspace({
              ...workspace,
              campaign_setup: {
                ...workspace.campaign_setup,
                schedule: {
                  ...workspace.campaign_setup.schedule,
                  preferred_hours_utc: parseCsv(String(data.value || '')).map((item) => Number(item)).filter((item) => Number.isFinite(item)),
                },
              },
            })}
            disabled={readOnly}
          />
          <Button
            appearance="primary"
            disabled={readOnly || saving || !canFinish}
            onClick={async () => {
              await saveWorkspacePatch({
                campaign_setup: workspace.campaign_setup,
                activation_complete: true,
              })
              onSavedInstance?.({
                nickname: workspace.induction.nickname,
                configured: true,
                goals_completed: true,
                hired_instance_id: selectedInstance.hired_instance_id,
                agent_type_id: selectedInstance.agent_type_id,
              })
              setSuccessMessage('Digital Marketing activation is runtime-ready.')
            }}
          >
            {saving ? 'Finishing…' : 'Finish activation'}
          </Button>
        </div>
      ) : null}
    </div>
  )
}
