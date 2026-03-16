import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardHeader, Text, Body1, Button, Table, TableHeader, TableRow, TableHeaderCell, TableBody, TableCell, Field, Textarea, Divider, Input } from '@fluentui/react-components'
import ApiErrorPanel from '../components/ApiErrorPanel'
import { gatewayApiClient, type AgentAuthoringDraft, type CatalogRelease } from '../services/gatewayApiClient'

type PlantAgent = {
  id: string
  name?: string
  industry?: string
  industry_id?: string
  status?: string
  team_id?: string | null
  team_name?: string | null
  created_at?: string
}

const AUTHORING_STAGE_LABELS: Record<string, string> = {
  define_agent: 'Define agent',
  operating_contract: 'Set operating contract',
  deliverables: 'Review deliverables',
  governance: 'Governance and handoff'
}

function humanizeLifecycleState(value?: string): string {
  if (!value) return 'Draft'
  return value.replace(/_/g, ' ')
}

function summarizeDraftReadiness(draft?: AgentAuthoringDraft | null) {
  const values = Object.values(draft?.section_states || {})
  return {
    ready: values.filter((value) => value === 'ready').length,
    needsReview: values.filter((value) => value === 'needs_review').length,
    missing: values.filter((value) => value === 'missing').length,
  }
}

function nextStepCopyForDraft(draft?: AgentAuthoringDraft | null): string {
  if (!draft) return 'Load a Base Agent Contract draft to review its status, completeness, and next step.'
  if (draft.status === 'approved') return 'Approval unlocked catalog preparation. Continue on the release board below when you are ready.'
  if (draft.status === 'changes_requested') return 'Open the Base Agent Contract Workflow, address the requested sections, save, and resubmit this draft.'
  if (draft.status === 'in_review') return 'Review the contract completeness, request changes with section-tied feedback, or approve it for catalog preparation.'
  if (summarizeDraftReadiness(draft).missing > 0) return 'Mandatory sections are still missing. Keep the draft in authoring until every required stage is ready.'
  return 'This draft is complete enough to move into review whenever the operator is ready.'
}

export default function AgentManagement() {
  const [agents, setAgents] = useState<PlantAgent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<unknown>(null)

  const [catalogReleases, setCatalogReleases] = useState<CatalogRelease[]>([])
  const [catalogLoading, setCatalogLoading] = useState(true)
  const [catalogError, setCatalogError] = useState<unknown>(null)
  const [catalogBusy, setCatalogBusy] = useState(false)
  const [selectedAgentId, setSelectedAgentId] = useState<string>('')
  const [selectedReleaseId, setSelectedReleaseId] = useState<string>('')
  const [catalogForm, setCatalogForm] = useState({
    public_name: 'Digital Marketing Agent',
    short_description: '',
    monthly_price_inr: '12000',
    trial_days: '7',
    allowed_durations: 'monthly, quarterly',
    supported_channels: 'youtube',
    approval_mode: 'manual_review',
    external_catalog_version: 'v1',
    agent_type_id: 'marketing.digital_marketing.v1',
    internal_definition_version_id: ''
  })

  const [agentTypes, setAgentTypes] = useState<any[]>([])
  const [agentTypesLoading, setAgentTypesLoading] = useState(true)
  const [agentTypesError, setAgentTypesError] = useState<unknown>(null)
  const [editorId, setEditorId] = useState<string>('')
  const [editorRaw, setEditorRaw] = useState<string>('')
  const [publishBusy, setPublishBusy] = useState(false)
  const [authoringDrafts, setAuthoringDrafts] = useState<AgentAuthoringDraft[]>([])
  const [authoringLoading, setAuthoringLoading] = useState(true)
  const [authoringError, setAuthoringError] = useState<unknown>(null)
  const [authoringBusy, setAuthoringBusy] = useState(false)
  const [selectedDraftId, setSelectedDraftId] = useState<string>('')
  const [feedbackSectionKey, setFeedbackSectionKey] = useState<string>('define_agent')
  const [feedbackComment, setFeedbackComment] = useState<string>('')
  const [reviewBoardMessage, setReviewBoardMessage] = useState<string>('')

  useEffect(() => {
    const abortController = new AbortController()

    async function loadAgents() {
      setIsLoading(true)
      setError(null)
      try {
        const data = (await gatewayApiClient.listAgents()) as PlantAgent[]
        setAgents(Array.isArray(data) ? data : [])
      } catch (e: any) {
        if (e?.name === 'AbortError') return
        setError(e)
        setAgents([])
      } finally {
        setIsLoading(false)
      }
    }

    void loadAgents()
    return () => abortController.abort()
  }, [])

  useEffect(() => {
    let cancelled = false

    async function loadAgentTypes() {
      setAgentTypesLoading(true)
      setAgentTypesError(null)
      try {
        const data = (await gatewayApiClient.listAgentTypeDefinitions()) as any[]
        if (cancelled) return
        setAgentTypes(Array.isArray(data) ? data : [])
      } catch (e: any) {
        if (cancelled) return
        setAgentTypesError(e)
        setAgentTypes([])
      } finally {
        if (!cancelled) setAgentTypesLoading(false)
      }
    }

    void loadAgentTypes()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    async function loadAuthoringDrafts() {
      setAuthoringLoading(true)
      setAuthoringError(null)
      try {
        const data = await gatewayApiClient.listAgentAuthoringDrafts()
        if (cancelled) return
        const drafts = Array.isArray(data) ? data : []
        setAuthoringDrafts(drafts)
      } catch (e: any) {
        if (cancelled) return
        setAuthoringError(e)
        setAuthoringDrafts([])
      } finally {
        if (!cancelled) setAuthoringLoading(false)
      }
    }

    void loadAuthoringDrafts()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    async function loadCatalogReleases() {
      setCatalogLoading(true)
      setCatalogError(null)
      try {
        const data = await gatewayApiClient.listCatalogReleases()
        if (cancelled) return
        setCatalogReleases(Array.isArray(data) ? data : [])
      } catch (e: any) {
        if (cancelled) return
        setCatalogError(e)
        setCatalogReleases([])
      } finally {
        if (!cancelled) setCatalogLoading(false)
      }
    }

    void loadCatalogReleases()
    return () => {
      cancelled = true
    }
  }, [])

  const releaseIndex = useMemo(() => {
    const entries = new Map<string, CatalogRelease>()
    for (const release of catalogReleases) {
      entries.set(release.id, release)
    }
    return entries
  }, [catalogReleases])

  const releaseBoardAgents = useMemo(() => {
    const preferred = agents.filter((agent) => {
      const name = String(agent.name || '').toLowerCase()
      const industry = String(agent.industry || agent.industry_id || '').toLowerCase()
      return name.includes('digital marketing') || industry.includes('marketing') || String(agent.id).toUpperCase().startsWith('AGT-MKT-')
    })
    return preferred.length > 0 ? preferred : agents
  }, [agents])

  const selectedAuthoringDraft = useMemo(() => {
    if (!authoringDrafts.length) return null
    return authoringDrafts.find((draft) => draft.draft_id === selectedDraftId) || authoringDrafts[0]
  }, [authoringDrafts, selectedDraftId])

  const selectedAuthoringSummary = useMemo(
    () => summarizeDraftReadiness(selectedAuthoringDraft),
    [selectedAuthoringDraft]
  )

  const actionableFeedback = selectedAuthoringDraft?.reviewer_comments || []

  useEffect(() => {
    if (selectedAgentId) return
    const first = releaseBoardAgents[0]
    if (!first) return
    selectAgentForCatalog(first.id)
  }, [releaseBoardAgents, selectedAgentId, releaseIndex])

  useEffect(() => {
    if (selectedDraftId) return
    const preferredDraft = authoringDrafts.find((draft) => draft.candidate_agent_type_id === 'marketing.digital_marketing.v1')
      || authoringDrafts[0]
    if (!preferredDraft) return
    setSelectedDraftId(preferredDraft.draft_id)
  }, [authoringDrafts, selectedDraftId])

  useEffect(() => {
    if (!selectedAuthoringDraft) return
    const sectionKeys = Object.keys(selectedAuthoringDraft.section_states || {})
    if (!sectionKeys.length) return
    if (!sectionKeys.includes(feedbackSectionKey)) {
      setFeedbackSectionKey(sectionKeys[0])
    }
  }, [selectedAuthoringDraft, feedbackSectionKey])

  const editorJsonError = useMemo(() => {
    if (!editorRaw.trim()) return null
    try {
      JSON.parse(editorRaw)
      return null
    } catch (e: any) {
      return String(e?.message || 'Invalid JSON')
    }
  }, [editorRaw])

  const editorSkillKeysError = useMemo(() => {
    if (!editorRaw.trim()) return null
    if (editorJsonError) return null
    try {
      const parsed = JSON.parse(editorRaw)
      const keys = parsed?.required_skill_keys
      if (!Array.isArray(keys)) return 'required_skill_keys must be a string[]'
      if (keys.length === 0) return 'required_skill_keys must include at least one skill_key'
      const bad = keys.filter((k: any) => typeof k !== 'string' || !String(k).trim())
      if (bad.length > 0) return 'required_skill_keys must contain only non-empty strings'
      return null
    } catch {
      return null
    }
  }, [editorRaw, editorJsonError])

  async function handleEditAgentType(agentTypeId: string) {
    setAgentTypesError(null)
    try {
      const data = await gatewayApiClient.getAgentTypeDefinition(agentTypeId)
      setEditorId(agentTypeId)
      setEditorRaw(JSON.stringify(data, null, 2))
    } catch (e: any) {
      setAgentTypesError(e)
    }
  }

  async function handlePublish() {
    if (!editorId.trim()) return
    if (editorJsonError) return
    if (editorSkillKeysError) return

    setPublishBusy(true)
    setAgentTypesError(null)
    try {
      const parsed = JSON.parse(editorRaw)
      const saved = await gatewayApiClient.publishAgentTypeDefinition(editorId, parsed)
      setEditorRaw(JSON.stringify(saved, null, 2))
      const refreshed = (await gatewayApiClient.listAgentTypeDefinitions()) as any[]
      setAgentTypes(Array.isArray(refreshed) ? refreshed : [])
    } catch (e: any) {
      setAgentTypesError(e)
    } finally {
      setPublishBusy(false)
    }
  }

  function upsertDraft(updatedDraft: AgentAuthoringDraft) {
    setAuthoringDrafts((current) => {
      const existingIndex = current.findIndex((draft) => draft.draft_id === updatedDraft.draft_id)
      if (existingIndex === -1) return [updatedDraft, ...current]
      const next = [...current]
      next[existingIndex] = updatedDraft
      return next
    })
    setSelectedDraftId(updatedDraft.draft_id)
  }

  async function handleSubmitAuthoringDraft() {
    if (!selectedAuthoringDraft) return
    setAuthoringBusy(true)
    setAuthoringError(null)
    try {
      const updatedDraft = await gatewayApiClient.submitAgentAuthoringDraft(selectedAuthoringDraft.draft_id)
      upsertDraft(updatedDraft)
      setReviewBoardMessage('Draft submitted for review. Reviewers can now inspect section readiness and decide whether to approve or request changes.')
    } catch (e: any) {
      setAuthoringError(e)
    } finally {
      setAuthoringBusy(false)
    }
  }

  async function handleRequestChanges() {
    if (!selectedAuthoringDraft) return
    if (!feedbackComment.trim()) {
      setAuthoringError(new Error('Reviewer feedback is required before sending a draft back.'))
      return
    }

    setAuthoringBusy(true)
    setAuthoringError(null)
    try {
      const updatedDraft = await gatewayApiClient.requestAgentAuthoringChanges(selectedAuthoringDraft.draft_id, {
        reviewer_name: 'PP Review Board',
        reviewer_comments: [
          {
            section_key: feedbackSectionKey,
            comment: feedbackComment.trim(),
            severity: 'changes_requested'
          }
        ]
      })
      upsertDraft(updatedDraft)
      setFeedbackComment('')
      setReviewBoardMessage(`Changes requested for ${AUTHORING_STAGE_LABELS[feedbackSectionKey] || feedbackSectionKey}. Return path: reopen the Base Agent Contract Workflow and update that section before resubmitting.`)
    } catch (e: any) {
      setAuthoringError(e)
    } finally {
      setAuthoringBusy(false)
    }
  }

  async function handleApproveAuthoringDraft() {
    if (!selectedAuthoringDraft) return
    setAuthoringBusy(true)
    setAuthoringError(null)
    try {
      const updatedDraft = await gatewayApiClient.approveAgentAuthoringDraft(selectedAuthoringDraft.draft_id, {
        reviewer_name: 'PP Review Board'
      })
      upsertDraft(updatedDraft)
      setReviewBoardMessage('Approved. This contract is now ready for catalog preparation on the release board below.')
    } catch (e: any) {
      setAuthoringError(e)
    } finally {
      setAuthoringBusy(false)
    }
  }

  function toCsv(value: string[]) {
    return value.join(', ')
  }

  function selectAgentForCatalog(agentId: string) {
    const release = releaseIndex.get(agentId)
    const fallbackAgent = agents.find((candidate) => candidate.id === agentId)
    setSelectedAgentId(agentId)
    setSelectedReleaseId(release?.release_id || '')
    setCatalogForm({
      public_name: release?.public_name || fallbackAgent?.name || 'Digital Marketing Agent',
      short_description: release?.short_description || 'Hire-ready Digital Marketing Agent release for platform-approved campaign execution.',
      monthly_price_inr: String(release?.monthly_price_inr || 12000),
      trial_days: String(release?.trial_days || 7),
      allowed_durations: toCsv(release?.allowed_durations || ['monthly', 'quarterly']),
      supported_channels: toCsv(release?.supported_channels || ['youtube']),
      approval_mode: release?.approval_mode || 'manual_review',
      external_catalog_version: release?.external_catalog_version || 'v1',
      agent_type_id: release?.agent_type_id || 'marketing.digital_marketing.v1',
      internal_definition_version_id: release?.internal_definition_version_id || ''
    })
  }

  function updateCatalogField(field: keyof typeof catalogForm, value: string) {
    setCatalogForm((current) => ({ ...current, [field]: value }))
  }

  async function refreshCatalogReleases(selectAgentId?: string) {
    const releases = await gatewayApiClient.listCatalogReleases()
    setCatalogReleases(Array.isArray(releases) ? releases : [])
    const agentToSelect = selectAgentId || selectedAgentId
    if (agentToSelect) {
      const release = (Array.isArray(releases) ? releases : []).find((candidate) => candidate.id === agentToSelect)
      setSelectedReleaseId(release?.release_id || '')
    }
  }

  async function handleSaveCatalogRelease() {
    if (!selectedAgentId) return
    setCatalogBusy(true)
    setCatalogError(null)
    try {
      await gatewayApiClient.upsertCatalogRelease(selectedAgentId, {
        public_name: catalogForm.public_name.trim(),
        short_description: catalogForm.short_description.trim(),
        monthly_price_inr: Number(catalogForm.monthly_price_inr || 0),
        trial_days: Number(catalogForm.trial_days || 0),
        allowed_durations: catalogForm.allowed_durations.split(',').map((entry) => entry.trim()).filter(Boolean),
        supported_channels: catalogForm.supported_channels.split(',').map((entry) => entry.trim()).filter(Boolean),
        approval_mode: catalogForm.approval_mode.trim(),
        external_catalog_version: catalogForm.external_catalog_version.trim(),
        agent_type_id: catalogForm.agent_type_id.trim(),
        internal_definition_version_id: catalogForm.internal_definition_version_id.trim() || undefined
      })
      await refreshCatalogReleases(selectedAgentId)
      selectAgentForCatalog(selectedAgentId)
    } catch (e: any) {
      setCatalogError(e)
    } finally {
      setCatalogBusy(false)
    }
  }

  async function handleApproveCatalogRelease() {
    if (!selectedAgentId) return
    setCatalogBusy(true)
    setCatalogError(null)
    try {
      await gatewayApiClient.approveCatalogRelease(selectedAgentId)
      await refreshCatalogReleases(selectedAgentId)
      selectAgentForCatalog(selectedAgentId)
    } catch (e: any) {
      setCatalogError(e)
    } finally {
      setCatalogBusy(false)
    }
  }

  async function handleRetireCatalogRelease() {
    if (!selectedReleaseId) return
    setCatalogBusy(true)
    setCatalogError(null)
    try {
      await gatewayApiClient.retireCatalogRelease(selectedReleaseId)
      await refreshCatalogReleases(selectedAgentId)
      selectAgentForCatalog(selectedAgentId)
    } catch (e: any) {
      setCatalogError(e)
    } finally {
      setCatalogBusy(false)
    }
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">Agent Management</Text>
        <Body1>Create, certify, and deploy AI agents</Body1>
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
        <Link to="/agents" style={{ textDecoration: 'none' }}>
          <Button appearance="primary">Agents</Button>
        </Link>
        <Link to="/agents/data" style={{ textDecoration: 'none' }}>
          <Button appearance="secondary">Agent Data</Button>
        </Link>
      </div>

      <Card>
        <CardHeader header={<Text weight="semibold">All Agents</Text>} />
        {isLoading && (
          <div style={{ padding: 16 }}>
            <Text>Loading from Plant…</Text>
          </div>
        )}

        {!!error && <ApiErrorPanel title="Plant error" error={error} />}

        <Table>
          <TableHeader>
            <TableRow>
              <TableHeaderCell>Name</TableHeaderCell>
              <TableHeaderCell>Industry</TableHeaderCell>
              <TableHeaderCell>Status</TableHeaderCell>
              <TableHeaderCell>Team</TableHeaderCell>
              <TableHeaderCell>Actions</TableHeaderCell>
            </TableRow>
          </TableHeader>
          <TableBody>
            {agents.map(agent => (
              <TableRow key={agent.id}>
                <TableCell>{agent.name || agent.id}</TableCell>
                <TableCell>{agent.industry || agent.industry_id || '-'}</TableCell>
                <TableCell>{agent.status || '-'}</TableCell>
                <TableCell>{agent.team_name || agent.team_id || '-'}</TableCell>
                <TableCell>
                  <Button size="small" appearance="subtle">Manage</Button>
                </TableCell>
              </TableRow>
            ))}

            {!isLoading && !error && agents.length === 0 && (
              <TableRow>
                <TableCell colSpan={5}>
                  <Text>No agents returned from Plant.</Text>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>

      {/* PP-FIX-1: DEF-015 audit — no hardcoded AGT-* IDs found; agents sourced from listAgents() */}
      <Divider style={{ margin: '24px 0' }} />

      <Card>
        <CardHeader header={<Text weight="semibold">Base Agent Contract Review Board</Text>} />

        <div style={{ padding: 16, display: 'grid', gap: 16, gridTemplateColumns: 'minmax(320px, 1fr) minmax(420px, 1.4fr)' }}>
          <div>
            <Text size={300} weight="medium">Reviewable drafts</Text>
            <Body1 style={{ marginTop: 6, marginBottom: 12 }}>
              Review state stays in Plant. PP makes the draft status, readiness, and next operator action explicit.
            </Body1>

            {authoringLoading && <Text>Loading Base Agent Contract drafts…</Text>}
            {!!authoringError && <ApiErrorPanel title="Authoring review error" error={authoringError} />}

            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {authoringDrafts.map((draft) => {
                const summary = summarizeDraftReadiness(draft)
                const isSelected = selectedAuthoringDraft?.draft_id === draft.draft_id
                return (
                  <button
                    key={draft.draft_id}
                    type="button"
                    onClick={() => {
                      setSelectedDraftId(draft.draft_id)
                      setReviewBoardMessage('')
                    }}
                    style={{
                      textAlign: 'left',
                      borderRadius: 12,
                      border: isSelected ? '1px solid var(--colorBrandStroke1)' : '1px solid var(--colorNeutralStroke2)',
                      background: isSelected ? 'var(--colorNeutralBackground1Selected)' : 'var(--colorNeutralBackground1)',
                      padding: 12,
                      cursor: 'pointer'
                    }}
                    data-testid={`agent-authoring-draft-${draft.draft_id}`}
                  >
                    <Text weight="medium">{draft.candidate_agent_label}</Text>
                    <Text size={200} style={{ display: 'block', opacity: 0.8, marginTop: 4 }}>
                      {humanizeLifecycleState(draft.status)} · {summary.ready} ready · {summary.missing} missing
                    </Text>
                    <Text size={200} style={{ display: 'block', opacity: 0.7, marginTop: 4 }}>
                      {draft.candidate_agent_type_id} · updated {new Date(draft.updated_at).toLocaleString()}
                    </Text>
                  </button>
                )
              })}

              {!authoringLoading && !authoringError && authoringDrafts.length === 0 && (
                <Text>No Base Agent Contract drafts are available yet. Start from the authoring workflow to create one.</Text>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <Text size={300} weight="medium">Review workspace</Text>

            <div className="pp-agent-setup-summary-grid">
              <Card className="pp-agent-setup-card">
                <div className="pp-agent-setup-metric">{humanizeLifecycleState(selectedAuthoringDraft?.status || 'draft')}</div>
                <div className="pp-agent-setup-label">Current review state</div>
              </Card>
              <Card className="pp-agent-setup-card">
                <div className="pp-agent-setup-metric">{selectedAuthoringSummary.ready}/4</div>
                <div className="pp-agent-setup-label">Mandatory stages ready</div>
              </Card>
              <Card className="pp-agent-setup-card">
                <div className="pp-agent-setup-metric">{selectedAuthoringSummary.missing}</div>
                <div className="pp-agent-setup-label">Blocking sections</div>
              </Card>
            </div>

            <Card>
              <CardHeader header={<Text weight="semibold">Contract completeness</Text>} />
              <div style={{ padding: 16, display: 'grid', gap: 10 }}>
                {selectedAuthoringDraft ? Object.entries(selectedAuthoringDraft.section_states).map(([sectionKey, state]) => (
                  <div
                    key={sectionKey}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '10px 12px',
                      borderRadius: 10,
                      border: '1px solid var(--colorNeutralStroke2)',
                      background: 'var(--colorNeutralBackground2)'
                    }}
                  >
                    <div>
                      <Text weight="medium">{AUTHORING_STAGE_LABELS[sectionKey] || sectionKey.replace(/_/g, ' ')}</Text>
                      <Text size={200} style={{ display: 'block', opacity: 0.8 }}>
                        {actionableFeedback.filter((comment) => comment.section_key === sectionKey).length} review item(s) tied to this stage
                      </Text>
                    </div>
                    <Text size={200}>{state.replace(/_/g, ' ')}</Text>
                  </div>
                )) : (
                  <Text>Select a draft to inspect section readiness.</Text>
                )}
              </div>
            </Card>

            <Card>
              <CardHeader header={<Text weight="semibold">Reviewer actions</Text>} />
              <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
                <Text size={200}>{nextStepCopyForDraft(selectedAuthoringDraft)}</Text>
                {!!reviewBoardMessage && (
                  <Text size={200} data-testid="agent-authoring-next-step">{reviewBoardMessage}</Text>
                )}

                <div style={{ display: 'grid', gap: 12, gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' }}>
                  <Field label="Feedback section">
                    <Input
                      value={feedbackSectionKey}
                      onChange={(_, data) => setFeedbackSectionKey(data.value)}
                      list="agent-authoring-section-keys"
                    />
                    <datalist id="agent-authoring-section-keys">
                      {selectedAuthoringDraft ? Object.keys(selectedAuthoringDraft.section_states).map((sectionKey) => (
                        <option key={sectionKey} value={sectionKey}>{AUTHORING_STAGE_LABELS[sectionKey] || sectionKey}</option>
                      )) : null}
                    </datalist>
                  </Field>
                  <Field label="Return path">
                    {selectedAuthoringDraft ? (
                      <Link to={`/agent-type-setup?draft_id=${encodeURIComponent(selectedAuthoringDraft.draft_id)}`} style={{ textDecoration: 'none' }}>
                        <Button appearance="secondary">Continue editing in workflow</Button>
                      </Link>
                    ) : (
                      <Text size={200}>Select a draft to open the authoring workflow.</Text>
                    )}
                  </Field>
                </div>

                <Field label="Reviewer feedback">
                  <Textarea
                    value={feedbackComment}
                    onChange={(_, data: any) => setFeedbackComment(data.value)}
                    rows={4}
                    placeholder="Explain exactly what the author needs to change and why."
                  />
                </Field>

                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                  <Button
                    appearance="primary"
                    onClick={handleSubmitAuthoringDraft}
                    disabled={authoringBusy || !selectedAuthoringDraft || selectedAuthoringDraft.status === 'in_review' || selectedAuthoringDraft.status === 'approved'}
                  >
                    Submit for review
                  </Button>
                  <Button
                    appearance="secondary"
                    onClick={handleRequestChanges}
                    disabled={authoringBusy || !selectedAuthoringDraft || selectedAuthoringDraft.status !== 'in_review'}
                  >
                    Request changes
                  </Button>
                  <Button
                    appearance="outline"
                    onClick={handleApproveAuthoringDraft}
                    disabled={authoringBusy || !selectedAuthoringDraft || selectedAuthoringDraft.status !== 'in_review'}
                  >
                    Approve contract
                  </Button>
                </div>
              </div>
            </Card>

            {actionableFeedback.length > 0 && (
              <Card>
                <CardHeader header={<Text weight="semibold">Actionable feedback</Text>} />
                <div style={{ padding: 16, display: 'grid', gap: 10 }}>
                  {actionableFeedback.map((comment, index) => (
                    <div
                      key={`${comment.section_key}-${index}-${comment.comment}`}
                      style={{
                        borderRadius: 12,
                        border: '1px solid var(--colorNeutralStroke2)',
                        padding: 12,
                        background: 'var(--colorNeutralBackground2)'
                      }}
                    >
                      <Text weight="medium">{AUTHORING_STAGE_LABELS[comment.section_key] || comment.section_key.replace(/_/g, ' ')}</Text>
                      <Text size={200} style={{ display: 'block', opacity: 0.8, marginTop: 4 }}>{comment.comment}</Text>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>
        </div>
      </Card>

      <Divider style={{ margin: '24px 0' }} />

      <Card>
        <CardHeader header={<Text weight="semibold">Digital Marketing Agent Release Board</Text>} />

        <div style={{ padding: 16, display: 'grid', gap: 16, gridTemplateColumns: 'minmax(320px, 1fr) minmax(420px, 1.4fr)' }}>
          <div>
            <Text size={300} weight="medium">Release candidates</Text>
            <Body1 style={{ marginTop: 6, marginBottom: 12 }}>
              PP is the review and release gate. Plant remains the source of lifecycle truth.
            </Body1>

            {catalogLoading && <Text>Loading catalog releases…</Text>}
            {!!catalogError && <ApiErrorPanel title="Catalog release error" error={catalogError} />}

            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {releaseBoardAgents.map((agent) => {
                const release = releaseIndex.get(agent.id)
                const isSelected = selectedAgentId === agent.id
                return (
                  <button
                    key={agent.id}
                    type="button"
                    onClick={() => selectAgentForCatalog(agent.id)}
                    style={{
                      textAlign: 'left',
                      borderRadius: 12,
                      border: isSelected ? '1px solid var(--colorBrandStroke1)' : '1px solid var(--colorNeutralStroke2)',
                      background: isSelected ? 'var(--colorNeutralBackground1Selected)' : 'var(--colorNeutralBackground1)',
                      padding: 12,
                      cursor: 'pointer'
                    }}
                  >
                    <Text weight="medium">{agent.name || agent.id}</Text>
                    <Text size={200} style={{ display: 'block', opacity: 0.8, marginTop: 4 }}>
                      {(release?.lifecycle_state || 'draft').replace(/_/g, ' ')}
                      {' · '}
                      {release?.approved_for_new_hire ? 'approved for new hire' : 'not approved'}
                    </Text>
                    <Text size={200} style={{ display: 'block', opacity: 0.7, marginTop: 4 }}>
                      {(release?.industry_name || agent.industry || agent.industry_id || 'unknown industry')} · {release?.job_role_label || 'release board candidate'}
                    </Text>
                  </button>
                )
              })}

              {!catalogLoading && releaseBoardAgents.length === 0 && (
                <Text>No Plant agents available to package into a hire-ready release.</Text>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <Text size={300} weight="medium">Recommended hire-ready fields</Text>

            <Field label="Public name">
              <Input value={catalogForm.public_name} onChange={(_, data) => updateCatalogField('public_name', data.value)} />
            </Field>

            <Field label="Short description">
              <Textarea value={catalogForm.short_description} onChange={(_, data: any) => updateCatalogField('short_description', data.value)} rows={3} />
            </Field>

            <div style={{ display: 'grid', gap: 12, gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' }}>
              <Field label="Monthly price (INR)">
                <Input value={catalogForm.monthly_price_inr} onChange={(_, data) => updateCatalogField('monthly_price_inr', data.value)} />
              </Field>
              <Field label="Trial days">
                <Input value={catalogForm.trial_days} onChange={(_, data) => updateCatalogField('trial_days', data.value)} />
              </Field>
            </div>

            <Field label="Allowed durations (comma separated)">
              <Input value={catalogForm.allowed_durations} onChange={(_, data) => updateCatalogField('allowed_durations', data.value)} />
            </Field>

            <Field label="Supported channels (comma separated)">
              <Input value={catalogForm.supported_channels} onChange={(_, data) => updateCatalogField('supported_channels', data.value)} />
            </Field>

            <div style={{ display: 'grid', gap: 12, gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' }}>
              <Field label="Approval mode">
                <Input value={catalogForm.approval_mode} onChange={(_, data) => updateCatalogField('approval_mode', data.value)} />
              </Field>
              <Field label="External catalog version">
                <Input value={catalogForm.external_catalog_version} onChange={(_, data) => updateCatalogField('external_catalog_version', data.value)} />
              </Field>
            </div>

            <div style={{ display: 'grid', gap: 12, gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' }}>
              <Field label="Agent type id">
                <Input value={catalogForm.agent_type_id} onChange={(_, data) => updateCatalogField('agent_type_id', data.value)} />
              </Field>
              <Field label="Definition version id">
                <Input value={catalogForm.internal_definition_version_id} onChange={(_, data) => updateCatalogField('internal_definition_version_id', data.value)} />
              </Field>
            </div>

            <Text size={200} style={{ opacity: 0.8 }}>
              Current status: {(releaseIndex.get(selectedAgentId)?.lifecycle_state || 'draft').replace(/_/g, ' ')}
              {selectedReleaseId ? ` · ${selectedReleaseId}` : ''}
            </Text>

            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <Button appearance="primary" onClick={handleSaveCatalogRelease} disabled={catalogBusy || !selectedAgentId}>
                Save release
              </Button>
              <Button appearance="secondary" onClick={handleApproveCatalogRelease} disabled={catalogBusy || !selectedAgentId}>
                Approve for CP
              </Button>
              <Button appearance="outline" onClick={handleRetireCatalogRelease} disabled={catalogBusy || !selectedReleaseId}>
                Retire from catalog
              </Button>
            </div>
          </div>
        </div>
      </Card>

      <Divider style={{ margin: '24px 0' }} />

      <Card>
        <CardHeader header={<Text weight="semibold">Agent Type Definitions</Text>} />

        {agentTypesLoading && (
          <div style={{ padding: 16 }}>
            <Text>Loading agent types…</Text>
          </div>
        )}

        {!!agentTypesError && <ApiErrorPanel title="AgentTypes error" error={agentTypesError} />}

        <Table>
          <TableHeader>
            <TableRow>
              <TableHeaderCell>Agent type</TableHeaderCell>
              <TableHeaderCell>Version</TableHeaderCell>
              <TableHeaderCell>Actions</TableHeaderCell>
            </TableRow>
          </TableHeader>
          <TableBody>
            {agentTypes.map((t) => (
              <TableRow key={String(t?.agent_type_id || '')}>
                <TableCell>{String(t?.agent_type_id || '-')}</TableCell>
                <TableCell>{String(t?.version || '-')}</TableCell>
                <TableCell>
                  <Button size="small" appearance="subtle" onClick={() => handleEditAgentType(String(t?.agent_type_id || ''))}>
                    Edit
                  </Button>
                </TableCell>
              </TableRow>
            ))}

            {!agentTypesLoading && !agentTypesError && agentTypes.length === 0 && (
              <TableRow>
                <TableCell colSpan={3}>
                  <Text>No agent types returned from Plant.</Text>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>

        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12, maxWidth: 900 }}>
          <Field label="Selected agent_type_id">
            <Textarea value={editorId} readOnly rows={1} />
          </Field>

          <Field label={editorJsonError ? `Definition JSON (error: ${editorJsonError})` : 'Definition JSON'}>
            <Textarea value={editorRaw} onChange={(_: unknown, data: any) => setEditorRaw(data.value)} rows={12} />
          </Field>

          <div>
            <Text size={200} style={{ display: 'block', opacity: 0.85 }}>
              Required field: <code>required_skill_keys</code> (string[] of certified skill_key values).
            </Text>
            {!!editorSkillKeysError && (
              <Text size={200} style={{ display: 'block', marginTop: 6, color: 'var(--colorPaletteRedForeground1)' }}>
                {editorSkillKeysError}
              </Text>
            )}
          </div>

          <div style={{ display: 'flex', gap: 12 }}>
            <Button appearance="primary" onClick={handlePublish} disabled={publishBusy || !editorId.trim() || !!editorJsonError || !!editorSkillKeysError}>
              Publish
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}
