// src/CP/FrontEnd/src/components/SkillsPanel.tsx
//
// Shows all skills assigned to a hired agent.
// For each skill, renders a GoalConfigForm driven by skill.goal_schema.
// Shows platform connections for skills that require them.
//
// CP-SKILLS-2: GoalConfigForm now persists goal_config via
// PATCH /api/cp/hired-agents/{id}/skills/{skill_id}/goal-config
// and seeds the form from skill.goal_config returned by the list endpoint.

import { useState, useEffect, useCallback } from 'react'
import { Button, Badge, Input, Select, Textarea, Checkbox } from '@fluentui/react-components'
import { LoadingIndicator, FeedbackMessage } from './FeedbackIndicators'
import {
  listHiredAgentSkills,
  saveGoalConfig,
  type AgentSkill,
  type GoalSchemaField,
} from '../services/agentSkills.service'
import {
  listPlatformConnections,
  createPlatformConnection,
  deletePlatformConnection,
  type PlatformConnection,
} from '../services/platformConnections.service'

// ── Helpers ───────────────────────────────────────────────────────────────────

function parseListText(value: string): string[] {
  return String(value || '')
    .split(/\n|,/g)
    .map((x) => x.trim())
    .filter(Boolean)
}

function safeJsonStringify(value: unknown): string {
  try {
    return JSON.stringify(value ?? {}, null, 2)
  } catch {
    return '{}'
  }
}

// ── ObjectFieldInput — own component so hooks are never called conditionally ──

interface ObjectFieldInputProps {
  field: GoalSchemaField
  value: unknown
  readOnly: boolean
  onChange: (key: string, value: unknown) => void
}

function ObjectFieldInput({ field, value, readOnly, onChange }: ObjectFieldInputProps) {
  const [localText, setLocalText] = useState(safeJsonStringify(value ?? {}))

  useEffect(() => {
    setLocalText(safeJsonStringify(value ?? {}))
  }, [value])

  const label = field.required ? `${field.label} *` : field.label

  return (
    <div style={{ marginBottom: '0.75rem' }}>
      <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>{label}</label>
      <Textarea
        value={localText}
        disabled={readOnly}
        onChange={(_, data) => {
          const raw = String(data.value || '')
          setLocalText(raw)
          try {
            const parsed = JSON.parse(raw || '{}')
            if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
              onChange(field.key, parsed)
            }
          } catch {
            /* keep raw until valid JSON */
          }
        }}
      />
      {field.description && (
        <div style={{ fontSize: '0.8rem', opacity: 0.7 }}>{field.description}</div>
      )}
    </div>
  )
}

// ── GoalFieldRenderer ─────────────────────────────────────────────────────────

interface GoalFieldRendererProps {
  field: GoalSchemaField
  value: unknown
  readOnly: boolean
  onChange: (key: string, value: unknown) => void
}

function GoalFieldRenderer({ field, value, readOnly, onChange }: GoalFieldRendererProps) {
  const label = field.required ? `${field.label} *` : field.label

  if (field.type === 'boolean') {
    return (
      <div style={{ marginBottom: '0.75rem' }}>
        <Checkbox
          label={label}
          checked={Boolean(value)}
          disabled={readOnly}
          onChange={(_, data) => onChange(field.key, Boolean(data.checked))}
        />
        {field.description && (
          <div style={{ fontSize: '0.8rem', opacity: 0.7 }}>{field.description}</div>
        )}
      </div>
    )
  }

  if (field.type === 'enum' && Array.isArray(field.options) && field.options.length > 0) {
    return (
      <div style={{ marginBottom: '0.75rem' }}>
        <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>{label}</label>
        <Select
          value={String(value ?? '')}
          disabled={readOnly}
          onChange={(_, data) => onChange(field.key, data.value)}
        >
          <option value="">— select —</option>
          {field.options.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </Select>
        {field.description && (
          <div style={{ fontSize: '0.8rem', opacity: 0.7 }}>{field.description}</div>
        )}
      </div>
    )
  }

  if (field.type === 'list') {
    const listValue = Array.isArray(value) ? (value as unknown[]) : []
    const text = listValue.map((x) => String(x ?? '')).join('\n')
    return (
      <div style={{ marginBottom: '0.75rem' }}>
        <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>{label}</label>
        <Textarea
          value={text}
          disabled={readOnly}
          placeholder="One per line"
          onChange={(_, data) => onChange(field.key, parseListText(String(data.value || '')))}
        />
        {field.description && (
          <div style={{ fontSize: '0.8rem', opacity: 0.7 }}>{field.description}</div>
        )}
      </div>
    )
  }

  if (field.type === 'object') {
    // Delegated to ObjectFieldInput to keep hook usage rules valid
    return (
      <ObjectFieldInput
        field={field}
        value={value}
        readOnly={readOnly}
        onChange={onChange}
      />
    )
  }

  // Default: text or number
  // TODO (CP-SKILLS-2): max_plan_gate is ignored here; enforcement is out of scope for CP-SKILLS-1.
  return (
    <div style={{ marginBottom: '0.75rem' }}>
      <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>{label}</label>
      <Input
        type={field.type === 'number' ? 'number' : 'text'}
        value={String(value ?? '')}
        disabled={readOnly}
        min={field.min}
        max={field.max}
        onChange={(_, data) =>
          onChange(field.key, field.type === 'number' ? Number(data.value) : data.value)
        }
      />
      {field.description && (
        <div style={{ fontSize: '0.8rem', opacity: 0.7 }}>{field.description}</div>
      )}
    </div>
  )
}

// ── GoalConfigForm ────────────────────────────────────────────────────────────

interface GoalConfigFormProps {
  skill: AgentSkill
  hiredInstanceId: string  // CP-SKILLS-2: needed to call PATCH endpoint
  readOnly: boolean
}

function GoalConfigForm({ skill, hiredInstanceId, readOnly }: GoalConfigFormProps) {
  const fields = skill.goal_schema?.fields ?? []
  // CP-SKILLS-2: seed form from persisted DB value; fall back to {} for first-time config
  const [values, setValues] = useState<Record<string, unknown>>(skill.goal_config ?? {})
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  if (fields.length === 0) {
    return (
      <div style={{ opacity: 0.6, fontSize: '0.9rem', paddingTop: '0.5rem' }}>
        No configurable goal fields for this skill.
      </div>
    )
  }

  const setField = (key: string, value: unknown) => {
    setSaved(false)
    setSaveError(null)
    setValues((prev) => ({ ...prev, [key]: value }))
  }

  const handleSave = async () => {
    setSaving(true)
    setSaved(false)
    setSaveError(null)
    try {
      await saveGoalConfig(hiredInstanceId, skill.skill_id, values)
      setSaved(true)
    } catch (e: unknown) {
      setSaveError(e instanceof Error ? e.message : 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <div style={{ fontWeight: 600, marginBottom: '0.5rem', fontSize: '0.9rem' }}>
        Goal Configuration
      </div>
      {fields.map((field) => (
        <GoalFieldRenderer
          key={field.key}
          field={field}
          value={values[field.key]}
          readOnly={readOnly}
          onChange={setField}
        />
      ))}
      {!readOnly && (
        <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <Button
            appearance="primary"
            size="small"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save goal config'}
          </Button>
          {saved && <span style={{ opacity: 0.7, fontSize: '0.85rem' }}>Saved ✓</span>}
          {saveError && (
            <span style={{ color: 'var(--colorPaletteRedForeground1)', fontSize: '0.85rem' }}>
              {saveError}
            </span>
          )}
        </div>
      )}
    </div>
  )
}

// ── PlatformConnectionsPanel ──────────────────────────────────────────────────

interface PlatformConnectionsPanelProps {
  hiredInstanceId: string
  requiredPlatforms?: string[]
  readOnly: boolean
}

function PlatformConnectionsPanel({
  hiredInstanceId,
  requiredPlatforms = [],
  readOnly,
}: PlatformConnectionsPanelProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [connections, setConnections] = useState<PlatformConnection[]>([])
  const [newPlatform, setNewPlatform] = useState('')
  const [newToken, setNewToken] = useState('')
  const [adding, setAdding] = useState(false)

  const loadConnections = useCallback(async () => {
    if (!hiredInstanceId) return
    setLoading(true)
    setError(null)
    try {
      const data = await listPlatformConnections(hiredInstanceId)
      setConnections(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load connections')
    } finally {
      setLoading(false)
    }
  }, [hiredInstanceId])

  useEffect(() => {
    loadConnections()
  }, [loadConnections])

  const handleAdd = async () => {
    if (!newPlatform.trim()) {
      setError('Platform name is required')
      return
    }
    setAdding(true)
    setError(null)
    try {
      const conn = await createPlatformConnection(hiredInstanceId, {
        skill_id: requiredPlatforms[0] ?? 'default',  // use first required platform's skill context
        platform_key: newPlatform.trim().toLowerCase(),
        credentials: newToken ? { access_token: newToken } : {},
      })
      setConnections((prev) => [...prev, conn])
      setNewPlatform('')
      setNewToken('')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to add connection')
    } finally {
      setAdding(false)
    }
  }

  const handleDelete = async (connectionId: string) => {
    setError(null)
    try {
      await deletePlatformConnection(hiredInstanceId, connectionId)
      setConnections((prev) => prev.filter((c) => c.id !== connectionId))
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to remove connection')
    }
  }

  return (
    <div style={{ marginTop: '0.75rem' }}>
      <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.5rem' }}>
        Platform Connections
        {requiredPlatforms.length > 0 && (
          <span style={{ marginLeft: '0.5rem', opacity: 0.7, fontWeight: 400 }}>
            (required: {requiredPlatforms.join(', ')})
          </span>
        )}
      </div>

      {loading && <LoadingIndicator message="Loading connections..." size="small" />}
      {error && <FeedbackMessage intent="error" title="Error" message={error} />}

      {!loading && connections.length === 0 && (
        <div style={{ opacity: 0.6, fontSize: '0.9rem' }}>No platforms connected yet.</div>
      )}

      {connections.map((conn) => (
        <div
          key={conn.id}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            marginBottom: '0.4rem',
            padding: '0.4rem 0.6rem',
            borderRadius: '6px',
            border: '1px solid var(--colorNeutralStroke2)',
          }}
        >
          <Badge appearance="tint" size="small">
            {conn.platform_key}
          </Badge>
          <span style={{ flex: 1, fontSize: '0.85rem', opacity: 0.8 }}>
            {conn.status ?? 'connected'}
          </span>
          {!readOnly && (
            <Button
              appearance="subtle"
              size="small"
              onClick={() => handleDelete(conn.id)}
            >
              Remove
            </Button>
          )}
        </div>
      ))}

      {!readOnly && (
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem', flexWrap: 'wrap' }}>
          <Input
            placeholder="Platform (e.g. linkedin)"
            value={newPlatform}
            onChange={(_, data) => setNewPlatform(String(data.value || ''))}
            style={{ width: '140px' }}
          />
          <Input
            placeholder="Access token (optional)"
            value={newToken}
            type="password"
            onChange={(_, data) => setNewToken(String(data.value || ''))}
            style={{ flex: 1, minWidth: '160px' }}
          />
          <Button
            appearance="outline"
            size="small"
            onClick={handleAdd}
            disabled={adding || !newPlatform.trim()}
          >
            {adding ? 'Adding...' : 'Add'}
          </Button>
        </div>
      )}
    </div>
  )
}

// ── SkillsPanel (main export) ─────────────────────────────────────────────────

interface SkillsPanelProps {
  hiredInstanceId: string
  readOnly: boolean
}

export function SkillsPanel({ hiredInstanceId, readOnly }: SkillsPanelProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [skills, setSkills] = useState<AgentSkill[]>([])
  const [expandedSkillId, setExpandedSkillId] = useState<string | null>(null)

  useEffect(() => {
    if (!hiredInstanceId) return
    let cancelled = false

    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await listHiredAgentSkills(hiredInstanceId)
        if (!cancelled) setSkills(data)
      } catch (e: unknown) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load skills')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [hiredInstanceId])

  if (!hiredInstanceId) {
    return (
      <div style={{ opacity: 0.6, fontSize: '0.9rem', paddingTop: '0.5rem' }}>
        No hired agent selected.
      </div>
    )
  }

  if (loading) return <LoadingIndicator message="Loading skills..." size="medium" />

  if (error) return <FeedbackMessage intent="error" title="Failed to load skills" message={error} />

  if (skills.length === 0) {
    return (
      <div style={{ opacity: 0.6, fontSize: '0.9rem', paddingTop: '0.5rem' }}>
        No skills configured for this agent yet.
      </div>
    )
  }

  return (
    <div>
      {skills.map((skill) => {
        const isExpanded = expandedSkillId === skill.skill_id
        const hasGoalSchema = (skill.goal_schema?.fields?.length ?? 0) > 0
        const requiresPlatforms = skill.goal_schema?.requires_platform_connections === true

        return (
          <div
            key={skill.skill_id}
            style={{
              marginBottom: '0.75rem',
              borderRadius: '10px',
              border: '1px solid var(--colorNeutralStroke2)',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.75rem 1rem',
                cursor: hasGoalSchema || requiresPlatforms ? 'pointer' : 'default',
                background: isExpanded ? 'var(--colorNeutralBackground2)' : undefined,
              }}
              onClick={() =>
                (hasGoalSchema || requiresPlatforms) &&
                setExpandedSkillId(isExpanded ? null : skill.skill_id)
              }
            >
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600 }}>{skill.display_name || skill.name}</div>
                {skill.description && (
                  <div style={{ fontSize: '0.85rem', opacity: 0.7 }}>{skill.description}</div>
                )}
              </div>
              {(hasGoalSchema || requiresPlatforms) && (
                <Button appearance="subtle" size="small">
                  {isExpanded ? 'Collapse ▲' : 'Configure ▼'}
                </Button>
              )}
            </div>

            {isExpanded && (
              <div
                style={{
                  padding: '0.75rem 1rem',
                  borderTop: '1px solid var(--colorNeutralStroke2)',
                }}
              >
                {hasGoalSchema && (
                  <GoalConfigForm
                    skill={skill}
                    hiredInstanceId={hiredInstanceId}
                    readOnly={readOnly}
                  />
                )}
                {requiresPlatforms && (
                  <PlatformConnectionsPanel
                    hiredInstanceId={hiredInstanceId}
                    readOnly={readOnly}
                  />
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

export default SkillsPanel
