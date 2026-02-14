import { useCallback, useEffect, useState } from 'react'
import {
  Card,
  CardHeader,
  Text,
  Body1,
  Button,
  Input,
  Textarea,
  Table,
  TableHeader,
  TableRow,
  TableHeaderCell,
  TableBody,
  TableCell
} from '@fluentui/react-components'
import ApiErrorPanel from '../components/ApiErrorPanel'
import { gatewayApiClient } from '../services/gatewayApiClient'

type PlantSkill = {
  id: string
  skill_key?: string
  name: string
  description?: string
  category?: string
  status?: string
  created_at?: string
}

type PlantJobRole = {
  id: string
  name: string
  description?: string
  required_skills?: string[]
  seniority_level?: string
  status?: string
  created_at?: string
}

export default function GenesisConsole() {
  const [skills, setSkills] = useState<PlantSkill[]>([])
  const [jobRoles, setJobRoles] = useState<PlantJobRole[]>([])
  const [skillsLoading, setSkillsLoading] = useState(true)
  const [rolesLoading, setRolesLoading] = useState(true)
  const [skillsError, setSkillsError] = useState<unknown>(null)
  const [rolesError, setRolesError] = useState<unknown>(null)

  const [createName, setCreateName] = useState('')
  const [createDescription, setCreateDescription] = useState('')
  const [createCategory, setCreateCategory] = useState('')
  const [createSkillKey, setCreateSkillKey] = useState('')
  const [createSubmitting, setCreateSubmitting] = useState(false)
  const [createError, setCreateError] = useState<unknown>(null)

  const loadSkills = useCallback(async (signal?: AbortSignal) => {
    setSkillsLoading(true)
    setSkillsError(null)
    try {
      const data = (await gatewayApiClient.listSkills({ limit: 200 })) as PlantSkill[]
      setSkills(Array.isArray(data) ? data : [])
    } catch (e: any) {
      if (e?.name === 'AbortError' || signal?.aborted) return
      setSkillsError(e)
      setSkills([])
    } finally {
      setSkillsLoading(false)
    }
  }, [])

  const loadJobRoles = useCallback(async (signal?: AbortSignal) => {
    setRolesLoading(true)
    setRolesError(null)
    try {
      const data = (await gatewayApiClient.listJobRoles({ limit: 200 })) as PlantJobRole[]
      setJobRoles(Array.isArray(data) ? data : [])
    } catch (e: any) {
      if (e?.name === 'AbortError' || signal?.aborted) return
      setRolesError(e)
      setJobRoles([])
    } finally {
      setRolesLoading(false)
    }
  }, [])

  useEffect(() => {
    const abortController = new AbortController()
    void loadSkills(abortController.signal)
    void loadJobRoles(abortController.signal)
    return () => abortController.abort()
  }, [loadSkills, loadJobRoles])

  const certifySkill = async (skillId: string) => {
    await gatewayApiClient.certifySkill(skillId, {})
    await loadSkills()
  }

  const certifyJobRole = async (jobRoleId: string) => {
    await gatewayApiClient.certifyJobRole(jobRoleId, {})
    await loadJobRoles()
  }

  const createSkill = async () => {
    const name = createName.trim()
    const description = createDescription.trim()
    const category = createCategory.trim()
    const skillKey = createSkillKey.trim()

    if (!name || !description || !category) return

    setCreateSubmitting(true)
    setCreateError(null)
    try {
      await gatewayApiClient.createSkill({
        name,
        description,
        category,
        skill_key: skillKey ? skillKey : undefined
      })
      setCreateName('')
      setCreateDescription('')
      setCreateCategory('')
      setCreateSkillKey('')
      await loadSkills()
    } catch (e) {
      setCreateError(e)
    } finally {
      setCreateSubmitting(false)
    }
  }

  const createDisabled = createSubmitting || !createName.trim() || !createDescription.trim() || !createCategory.trim()

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">Genesis Console</Text>
        <Body1>Skill & job role certification via Plant Genesis</Body1>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '24px' }}>
        <Card>
          <CardHeader
            header={<Text weight="semibold">Skills</Text>}
            description={<Text size={200}>{skillsLoading ? 'Loading…' : `${skills.length} total`}</Text>}
            action={
              <Button appearance="subtle" size="small" onClick={() => void loadSkills()}>
                Refresh
              </Button>
            }
          />

          <div style={{ padding: 16, display: 'grid', gap: 12, gridTemplateColumns: '1fr 1fr' }}>
            <div>
              <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Name</Text>
              <Input value={createName} onChange={(_, data) => setCreateName(data.value)} placeholder="Skill name" />
            </div>
            <div>
              <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Category</Text>
              <Input value={createCategory} onChange={(_, data) => setCreateCategory(data.value)} placeholder="technical | soft_skill | domain_expertise" />
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Description</Text>
              <Textarea value={createDescription} onChange={(_, data) => setCreateDescription((data as any).value)} placeholder="What this skill covers" rows={3} />
            </div>
            <div>
              <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Skill Key (optional)</Text>
              <Input value={createSkillKey} onChange={(_, data) => setCreateSkillKey(data.value)} placeholder="python-3-11" />
            </div>
            <div style={{ display: 'flex', alignItems: 'end', justifyContent: 'flex-end' }}>
              <Button appearance="primary" onClick={() => void createSkill()} disabled={createDisabled}>
                {createSubmitting ? 'Creating…' : 'Create'}
              </Button>
            </div>
          </div>

          {createError && <div style={{ padding: 16 }}><ApiErrorPanel title="Create skill error" error={createError} /></div>}

          {skillsError && <div style={{ padding: 16 }}><ApiErrorPanel title="Skills error" error={skillsError} /></div>}

          <Table>
            <TableHeader>
              <TableRow>
                <TableHeaderCell>Name</TableHeaderCell>
                <TableHeaderCell>Skill Key</TableHeaderCell>
                <TableHeaderCell>Category</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
                <TableHeaderCell>Actions</TableHeaderCell>
              </TableRow>
            </TableHeader>
            <TableBody>
              {skills.map(skill => (
                <TableRow key={skill.id}>
                  <TableCell>{skill.name || skill.id}</TableCell>
                  <TableCell>{skill.skill_key || '-'}</TableCell>
                  <TableCell>{skill.category || '-'}</TableCell>
                  <TableCell>{skill.status || '-'}</TableCell>
                  <TableCell>
                    <Button
                      size="small"
                      appearance="primary"
                      disabled={(skill.status || '').toLowerCase() === 'certified'}
                      onClick={() => void certifySkill(skill.id)}
                    >
                      Certify
                    </Button>
                  </TableCell>
                </TableRow>
              ))}

              {!skillsLoading && !skillsError && skills.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5}>
                    <Text>No skills returned from Plant.</Text>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </Card>

        <Card>
          <CardHeader
            header={<Text weight="semibold">Job Roles</Text>}
            description={<Text size={200}>{rolesLoading ? 'Loading…' : `${jobRoles.length} total`}</Text>}
            action={
              <Button appearance="subtle" size="small" onClick={() => void loadJobRoles()}>
                Refresh
              </Button>
            }
          />

          {rolesError && <div style={{ padding: 16 }}><ApiErrorPanel title="Job roles error" error={rolesError} /></div>}

          <Table>
            <TableHeader>
              <TableRow>
                <TableHeaderCell>Name</TableHeaderCell>
                <TableHeaderCell>Seniority</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
                <TableHeaderCell>Required Skills</TableHeaderCell>
                <TableHeaderCell>Actions</TableHeaderCell>
              </TableRow>
            </TableHeader>
            <TableBody>
              {jobRoles.map(role => (
                <TableRow key={role.id}>
                  <TableCell>{role.name || role.id}</TableCell>
                  <TableCell>{role.seniority_level || '-'}</TableCell>
                  <TableCell>{role.status || '-'}</TableCell>
                  <TableCell>{Array.isArray(role.required_skills) ? role.required_skills.length : 0}</TableCell>
                  <TableCell>
                    <Button
                      size="small"
                      appearance="primary"
                      disabled={(role.status || '').toLowerCase() === 'certified'}
                      onClick={() => void certifyJobRole(role.id)}
                    >
                      Certify
                    </Button>
                  </TableCell>
                </TableRow>
              ))}

              {!rolesLoading && !rolesError && jobRoles.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5}>
                    <Text>No job roles returned from Plant.</Text>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </Card>
      </div>
    </div>
  )
}
