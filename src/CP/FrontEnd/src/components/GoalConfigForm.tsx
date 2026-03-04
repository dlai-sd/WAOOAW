// src/CP/FrontEnd/src/components/GoalConfigForm.tsx
//
// Generic dynamic form rendered from a GoalSchema.
// Supports field types: text, number, boolean, enum, list, object.
// Supports show_if conditional display — a field with show_if is only shown
// when values[show_if.key] === show_if.value.
//
// CP-SKILLS-2 E6-S2: extracted from SkillsPanel.tsx so it can be tested and
// reused independently.

import { useState, useEffect, useCallback } from 'react'
import { Button, Input, Select, Textarea, Checkbox } from '@fluentui/react-components'
import { LoadingIndicator, FeedbackMessage } from './FeedbackIndicators'
import {
  listHiredAgentSkills,
  saveGoalConfig,
  type AgentSkill,
  type GoalSchemaField,
} from '../services/agentSkills.service'

// ── Helpers ──────────────────────────────────────────────────────────────────

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

// ── ObjectFieldInput ─────────────────────────────────────────────────────────
// Own component so hooks are never called conditionally.

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

// ── GoalFieldRenderer ────────────────────────────────────────────────────────

export interface GoalFieldRendererProps {
  field: GoalSchemaField
  value: unknown
  readOnly: boolean
  onChange: (key: string, value: unknown) => void
}

export function GoalFieldRenderer({ field, value, readOnly, onChange }: GoalFieldRendererProps) {
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

export interface GoalConfigFormProps {
  skill: AgentSkill
  hiredInstanceId: string
  readOnly: boolean
}

export function GoalConfigForm({ skill, hiredInstanceId, readOnly }: GoalConfigFormProps) {
  const fields = skill.goal_schema?.fields ?? []

  // Seed form from persisted DB value; fall back to {} for first-time config.
  const [values, setValues] = useState<Record<string, unknown>>(skill.goal_config ?? {})
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  // show_if: a field is visible only when its condition is met.
  const isVisible = (f: GoalSchemaField): boolean => {
    if (!f.show_if) return true
    return values[f.show_if.key] === f.show_if.value
  }

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
      {fields.map((field) =>
        isVisible(field) ? (
          <GoalFieldRenderer
            key={field.key}
            field={field}
            value={values[field.key]}
            readOnly={readOnly}
            onChange={setField}
          />
        ) : null
      )}
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

// ── SkillsGoalConfigSection ───────────────────────────────────────────────────
// Loads skills for a hired agent and renders one GoalConfigForm per skill.
// Used by the Skills tab in MyAgents.tsx (via SkillsPanel) AND can be used
// standalone in other contexts.

interface SkillsGoalConfigSectionProps {
  hiredInstanceId: string
  readOnly: boolean
}

export function SkillsGoalConfigSection({ hiredInstanceId, readOnly }: SkillsGoalConfigSectionProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [skills, setSkills] = useState<AgentSkill[]>([])

  const load = useCallback(async () => {
    if (!hiredInstanceId) return
    setLoading(true)
    setError(null)
    try {
      const data = await listHiredAgentSkills(hiredInstanceId)
      setSkills(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load skills')
    } finally {
      setLoading(false)
    }
  }, [hiredInstanceId])

  useEffect(() => {
    load()
  }, [load])

  if (!hiredInstanceId) return null
  if (loading) return <LoadingIndicator message="Loading skills..." size="medium" />
  if (error) return <FeedbackMessage intent="error" title="Failed to load skills" message={error} />

  const skillsWithGoals = skills.filter((s) => (s.goal_schema?.fields?.length ?? 0) > 0)

  if (skillsWithGoals.length === 0) {
    return (
      <div style={{ opacity: 0.6, fontSize: '0.9rem', paddingTop: '0.5rem' }}>
        No configurable goal fields for this agent.
      </div>
    )
  }

  return (
    <div>
      {skillsWithGoals.map((skill) => (
        <div
          key={skill.skill_id}
          style={{
            marginBottom: '1rem',
            padding: '0.75rem 1rem',
            borderRadius: '10px',
            border: '1px solid var(--colorNeutralStroke2)',
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: '0.5rem' }}>
            {skill.display_name || skill.name}
            {skill.description && (
              <div style={{ fontWeight: 400, fontSize: '0.85rem', opacity: 0.7 }}>
                {skill.description}
              </div>
            )}
          </div>
          <GoalConfigForm
            skill={skill}
            hiredInstanceId={hiredInstanceId}
            readOnly={readOnly}
          />
        </div>
      ))}
    </div>
  )
}

export default GoalConfigForm
