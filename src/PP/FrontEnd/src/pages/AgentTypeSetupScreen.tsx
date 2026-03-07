import { useEffect, useState } from 'react'
import {
  Body1,
  Button,
  Card,
  CardHeader,
  Checkbox,
  Field,
  Input,
  Spinner,
  Text,
  Textarea,
} from '@fluentui/react-components'
import ApiErrorPanel from '../components/ApiErrorPanel'
import { useAgentTypeSetup, HOOK_LIST, type AgentTypeSetupFormData } from '../services/useAgentTypeSetup'

const INDUSTRY_OPTIONS = [
  { value: 'marketing', label: 'Marketing' },
  { value: 'education', label: 'Education' },
  { value: 'sales', label: 'Sales' },
]

const DEFAULT_HOOKS: Record<string, boolean> = Object.fromEntries(
  HOOK_LIST.map(h => [h.key, h.key === 'AuditHook' ? true : false])
)

const DEFAULT_FORM: AgentTypeSetupFormData = {
  agent_type: '',
  display_name: '',
  description: '',
  industry: 'marketing',
  processor_class: '',
  pump_class: '',
  connector_class: '',
  publisher_class: '',
  approval_mode: 'manual',
  max_tasks_per_day: 10,
  max_position_size_inr: 0,
  trial_task_limit: 10,
  hooks: { ...DEFAULT_HOOKS },
}

interface ValidationErrors {
  agent_type?: string
  display_name?: string
  processor_class?: string
  pump_class?: string
}

function validate(form: AgentTypeSetupFormData): ValidationErrors {
  const errors: ValidationErrors = {}
  if (!form.agent_type.trim()) errors.agent_type = 'Agent type is required'
  if (!form.display_name.trim()) errors.display_name = 'Display name is required'
  if (!form.processor_class.trim()) errors.processor_class = 'Processor class is required'
  if (!form.pump_class.trim()) errors.pump_class = 'Pump class is required'
  return errors
}

const isTradingConnector = (cls: string) => cls.toLowerCase().includes('trading')

interface AgentTypeSetupScreenProps {
  agentSetupId?: string
}

export default function AgentTypeSetupScreen({ agentSetupId }: AgentTypeSetupScreenProps) {
  const [form, setForm] = useState<AgentTypeSetupFormData>({ ...DEFAULT_FORM })
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({})
  const [submitted, setSubmitted] = useState(false)

  const {
    isSubmitting,
    error,
    savedAt,
    processorOptions,
    pumpOptions,
    isLoadingOptions,
    loadClassOptions,
    submit,
  } = useAgentTypeSetup()

  useEffect(() => {
    void loadClassOptions()
  }, [loadClassOptions])

  function setField<K extends keyof AgentTypeSetupFormData>(key: K, value: AgentTypeSetupFormData[K]) {
    setForm(prev => ({ ...prev, [key]: value }))
  }

  async function handleSubmit() {
    const errors = validate(form)
    setValidationErrors(errors)
    if (Object.keys(errors).length > 0) return

    try {
      await submit(form, agentSetupId)
      setSubmitted(true)
    } catch {
      // error displayed via hook
    }
  }

  const showPositionSizeField = isTradingConnector(form.connector_class)

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">
          {agentSetupId ? 'Edit' : 'New'} Agent Type Setup
        </Text>
        <Body1>Configure agent identity, construct bindings, policy and hooks</Body1>
      </div>

      {!!error && <ApiErrorPanel title="Agent type setup error" error={error} />}

      {submitted && savedAt && (
        <div
          style={{
            padding: '12px 16px',
            background: 'rgba(16, 185, 129, 0.1)',
            borderRadius: 8,
            marginBottom: 16,
            border: '1px solid #10b981',
          }}
        >
          <Text style={{ color: '#10b981' }}>
            ✓ Saved at {new Date(savedAt).toLocaleString()}
          </Text>
        </div>
      )}

      {/* Section 1: Identity */}
      <Card style={{ marginBottom: 16 }}>
        <CardHeader header={<Text weight="semibold">1. Identity</Text>} />
        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12, maxWidth: 600 }}>
          <Field
            label="Agent type"
            required
            validationMessage={validationErrors.agent_type}
            validationState={validationErrors.agent_type ? 'error' : 'none'}
          >
            <Input
              value={form.agent_type}
              onChange={(_, d) => setField('agent_type', d.value)}
              placeholder="e.g. marketing_content_v1"
            />
          </Field>

          <Field
            label="Display name"
            required
            validationMessage={validationErrors.display_name}
            validationState={validationErrors.display_name ? 'error' : 'none'}
          >
            <Input
              value={form.display_name}
              onChange={(_, d) => setField('display_name', d.value)}
              placeholder="e.g. Content Marketing Agent"
            />
          </Field>

          <Field label="Description">
            <Textarea
              value={form.description}
              onChange={(_, d) => setField('description', d.value)}
              rows={3}
              placeholder="Brief description of this agent type"
            />
          </Field>

          <Field label="Industry">
            <select
              value={form.industry}
              onChange={e => setField('industry', e.target.value)}
              style={{
                padding: '6px 10px',
                borderRadius: 4,
                background: '#18181b',
                color: '#fff',
                border: '1px solid rgba(255,255,255,0.2)',
                width: '100%',
              }}
            >
              {INDUSTRY_OPTIONS.map(o => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </Field>
        </div>
      </Card>

      {/* Section 2: ConstructBindings */}
      <Card style={{ marginBottom: 16 }}>
        <CardHeader header={<Text weight="semibold">2. Construct Bindings</Text>} />
        {isLoadingOptions && (
          <div style={{ padding: 16 }}>
            <Spinner label="Loading class options..." />
          </div>
        )}
        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12, maxWidth: 600 }}>
          <Field
            label="Processor class"
            required
            validationMessage={validationErrors.processor_class}
            validationState={validationErrors.processor_class ? 'error' : 'none'}
          >
            <select
              value={form.processor_class}
              onChange={e => setField('processor_class', e.target.value)}
              style={{
                padding: '6px 10px',
                borderRadius: 4,
                background: '#18181b',
                color: '#fff',
                border: '1px solid rgba(255,255,255,0.2)',
                width: '100%',
              }}
            >
              <option value="">— Select processor class —</option>
              {processorOptions.length > 0
                ? processorOptions.map(o => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))
                : (
                    <option value={form.processor_class || 'ContentProcessor'}>
                      {form.processor_class || 'ContentProcessor'}
                    </option>
                  )}
            </select>
          </Field>

          <Field
            label="Pump class"
            required
            validationMessage={validationErrors.pump_class}
            validationState={validationErrors.pump_class ? 'error' : 'none'}
          >
            <select
              value={form.pump_class}
              onChange={e => setField('pump_class', e.target.value)}
              style={{
                padding: '6px 10px',
                borderRadius: 4,
                background: '#18181b',
                color: '#fff',
                border: '1px solid rgba(255,255,255,0.2)',
                width: '100%',
              }}
            >
              <option value="">— Select pump class —</option>
              {pumpOptions.length > 0
                ? pumpOptions.map(o => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))
                : (
                    <option value={form.pump_class || 'SocialMediaPump'}>
                      {form.pump_class || 'SocialMediaPump'}
                    </option>
                  )}
            </select>
          </Field>

          <Field label="Connector class (optional)">
            <Input
              value={form.connector_class}
              onChange={(_, d) => setField('connector_class', d.value)}
              placeholder="None"
            />
          </Field>

          <Field label="Publisher class (optional)">
            <Input
              value={form.publisher_class}
              onChange={(_, d) => setField('publisher_class', d.value)}
              placeholder="None"
            />
          </Field>
        </div>
      </Card>

      {/* Section 3: ConstraintPolicy */}
      <Card style={{ marginBottom: 16 }}>
        <CardHeader header={<Text weight="semibold">3. Constraint Policy</Text>} />
        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12, maxWidth: 600 }}>
          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 8, opacity: 0.85 }}>
              Approval mode
            </Text>
            <div style={{ display: 'flex', gap: 8 }}>
              <Button
                appearance={form.approval_mode === 'manual' ? 'primary' : 'secondary'}
                size="small"
                onClick={() => setField('approval_mode', 'manual')}
                aria-label="Manual approval mode"
              >
                Manual
              </Button>
              <Button
                appearance={form.approval_mode === 'auto' ? 'primary' : 'secondary'}
                size="small"
                onClick={() => setField('approval_mode', 'auto')}
                aria-label="Auto approval mode"
              >
                Auto
              </Button>
            </div>
          </div>

          <Field label="Max tasks per day (0 = unlimited)">
            <Input
              type="number"
              value={String(form.max_tasks_per_day)}
              onChange={(_, d) => setField('max_tasks_per_day', Number(d.value) || 0)}
            />
          </Field>

          {showPositionSizeField && (
            <Field label="Max position size (INR, 0 = unlimited)">
              <Input
                type="number"
                value={String(form.max_position_size_inr)}
                onChange={(_, d) => setField('max_position_size_inr', Number(d.value) || 0)}
              />
            </Field>
          )}

          <Field label="Trial task limit">
            <Input
              type="number"
              value={String(form.trial_task_limit)}
              onChange={(_, d) => setField('trial_task_limit', Number(d.value) || 10)}
            />
          </Field>
        </div>
      </Card>

      {/* Section 4: Hook Checklist */}
      <Card style={{ marginBottom: 16 }}>
        <CardHeader header={<Text weight="semibold">4. Hook Checklist</Text>} />
        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
          {HOOK_LIST.map(hook => (
            <div key={hook.key} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <Checkbox
                label={hook.label}
                checked={form.hooks[hook.key] ?? false}
                disabled={hook.key === 'AuditHook'}
                onChange={(_, d) => {
                  if (hook.key === 'AuditHook') return
                  setForm(prev => ({
                    ...prev,
                    hooks: { ...prev.hooks, [hook.key]: !!d.checked },
                  }))
                }}
              />
              <Text size={200} style={{ paddingLeft: 32, opacity: 0.7 }}>
                {hook.description}
              </Text>
            </div>
          ))}
        </div>
      </Card>

      <div style={{ display: 'flex', gap: 12, marginBottom: 32 }}>
        <Button
          appearance="primary"
          onClick={() => void handleSubmit()}
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Saving…' : agentSetupId ? 'Update' : 'Create'}
        </Button>
        <Button appearance="secondary" onClick={() => setForm({ ...DEFAULT_FORM, hooks: { ...DEFAULT_HOOKS } })}>
          Reset
        </Button>
      </div>
    </div>
  )
}
