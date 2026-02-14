import '@testing-library/jest-dom/vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { expect, test, vi } from 'vitest'

import GenesisConsole from './GenesisConsole'
import { GatewayApiError } from '../services/gatewayApiClient'

const mocks = vi.hoisted(() => {
  return {
    listSkills: vi.fn(async () => []),
    listJobRoles: vi.fn(async () => []),
    createSkill: vi.fn(async () => ({})),
    createJobRole: vi.fn(async () => ({})),
    certifySkill: vi.fn(async () => ({})),
    certifyJobRole: vi.fn(async () => ({}))
  }
})

vi.mock('../services/gatewayApiClient', () => {
  return vi.importActual<any>('../services/gatewayApiClient').then((actual) => {
    return {
      ...actual,
      gatewayApiClient: {
        ...(actual.gatewayApiClient || {}),
        listSkills: mocks.listSkills,
        listJobRoles: mocks.listJobRoles,
        createSkill: mocks.createSkill,
        createJobRole: mocks.createJobRole,
        certifySkill: mocks.certifySkill,
        certifyJobRole: mocks.certifyJobRole
      }
    }
  })
})

test('GenesisConsole renders empty state for skills and job roles', async () => {
  render(<GenesisConsole />)

  expect(await screen.findByText('No skills returned from Plant.')).toBeInTheDocument()
  expect(await screen.findByText('No job roles returned from Plant.')).toBeInTheDocument()

  expect(mocks.listSkills).toHaveBeenCalled()
  expect(mocks.listJobRoles).toHaveBeenCalled()
})

test('GenesisConsole shows skill_key in the skills table', async () => {
  mocks.listSkills.mockResolvedValueOnce([
    {
      id: 'skill-1',
      name: 'Python',
      category: 'technical',
      status: 'certified',
      skill_key: 'python'
    }
  ])

  render(<GenesisConsole />)

  await waitFor(() => {
    expect(screen.getByText('Python')).toBeInTheDocument()
  })

  expect(screen.getByText('python')).toBeInTheDocument()
})

test('GenesisConsole shows ApiErrorPanel on skill fetch errors', async () => {
  mocks.listSkills.mockRejectedValueOnce(new Error('boom'))

  render(<GenesisConsole />)

  await waitFor(() => {
    expect(screen.getByText('Skills error')).toBeInTheDocument()
  })
})

test('GenesisConsole disables Create until required fields are set', async () => {
  render(<GenesisConsole />)

  const createButton = await screen.findByRole('button', { name: 'Create' })
  expect(createButton).toBeDisabled()

  fireEvent.change(screen.getByPlaceholderText('Skill name'), { target: { value: 'Python' } })
  fireEvent.change(screen.getByPlaceholderText('technical | soft_skill | domain_expertise'), { target: { value: 'technical' } })
  fireEvent.change(screen.getByPlaceholderText('What this skill covers'), { target: { value: 'Modern Python programming' } })

  expect(screen.getByRole('button', { name: 'Create' })).toBeEnabled()
})

test('GenesisConsole shows ApiErrorPanel on create skill conflict (409)', async () => {
  mocks.createSkill.mockRejectedValueOnce(
    new GatewayApiError('Duplicate', {
      status: 409,
      problem: {
        type: 'about:blank',
        title: 'Conflict',
        status: 409,
        detail: 'Duplicate'
      }
    })
  )

  render(<GenesisConsole />)

  fireEvent.change(screen.getByPlaceholderText('Skill name'), { target: { value: 'Python' } })
  fireEvent.change(screen.getByPlaceholderText('technical | soft_skill | domain_expertise'), { target: { value: 'technical' } })
  fireEvent.change(screen.getByPlaceholderText('What this skill covers'), { target: { value: 'Modern Python programming' } })

  fireEvent.click(screen.getByRole('button', { name: 'Create' }))

  await waitFor(() => {
    expect(screen.getByText('Create skill error')).toBeInTheDocument()
  })
})

test('GenesisConsole certify skill triggers refresh and disables after certified', async () => {
  mocks.listSkills.mockReset()
  mocks.certifySkill.mockReset()

  let certified = false
  mocks.listSkills.mockImplementation(async () => [
    {
      id: 'skill-1',
      name: 'Python',
      category: 'technical',
      status: certified ? 'certified' : 'pending_certification',
      skill_key: 'python'
    }
  ])

  mocks.certifySkill.mockImplementation(async () => {
    certified = true
    return {}
  })

  render(<GenesisConsole />)

  await waitFor(() => {
    expect(screen.getByText('Python')).toBeInTheDocument()
  })

  const beforeRefreshCalls = mocks.listSkills.mock.calls.length
  fireEvent.click(screen.getByRole('button', { name: 'Certify' }))

  await waitFor(() => {
    expect(mocks.certifySkill).toHaveBeenCalledWith('skill-1', {})
    expect(mocks.listSkills.mock.calls.length).toBeGreaterThan(beforeRefreshCalls)
  })

  await waitFor(() => {
    expect(screen.getByRole('button', { name: 'Certify' })).toBeDisabled()
  })
})

test('GenesisConsole disables Create Role until required fields are set', async () => {
  mocks.listSkills.mockReset()
  mocks.listSkills.mockImplementation(async () => [
    {
      id: 'skill-1',
      name: 'Python',
      category: 'technical',
      status: 'certified',
      skill_key: 'python'
    }
  ])

  render(<GenesisConsole />)

  const createRoleButton = await screen.findByRole('button', { name: 'Create Role' })
  expect(createRoleButton).toBeDisabled()

  fireEvent.change(screen.getByPlaceholderText('Job role name'), { target: { value: 'Backend Engineer' } })
  fireEvent.change(screen.getByPlaceholderText('What this role does'), { target: { value: 'Build APIs' } })

  expect(createRoleButton).toBeDisabled()

  await screen.findByText(/python \(certified\)/i)
  fireEvent.click(screen.getByText(/python \(certified\)/i))

  expect(screen.getByRole('button', { name: 'Create Role' })).toBeEnabled()
})

test('GenesisConsole shows ApiErrorPanel on create job role conflict (409)', async () => {
  mocks.listSkills.mockReset()
  mocks.listSkills.mockImplementation(async () => [
    {
      id: 'skill-1',
      name: 'Python',
      category: 'technical',
      status: 'certified',
      skill_key: 'python'
    }
  ])

  mocks.createJobRole.mockRejectedValueOnce(
    new GatewayApiError('Duplicate', {
      status: 409,
      problem: {
        type: 'about:blank',
        title: 'Conflict',
        status: 409,
        detail: 'Duplicate'
      }
    })
  )

  render(<GenesisConsole />)

  fireEvent.change(screen.getByPlaceholderText('Job role name'), { target: { value: 'Backend Engineer' } })
  fireEvent.change(screen.getByPlaceholderText('What this role does'), { target: { value: 'Build APIs' } })

  await screen.findByText(/python \(certified\)/i)
  fireEvent.click(screen.getByText(/python \(certified\)/i))
  fireEvent.click(screen.getByRole('button', { name: 'Create Role' }))

  await waitFor(() => {
    expect(screen.getByText('Create job role error')).toBeInTheDocument()
  })
})

test('GenesisConsole create job role triggers refresh and renders new role', async () => {
  mocks.listSkills.mockReset()
  mocks.listSkills.mockImplementation(async () => [
    {
      id: 'skill-1',
      name: 'Python',
      category: 'technical',
      status: 'certified',
      skill_key: 'python'
    }
  ])

  let roles: any[] = []
  let created = false
  let listCallsAfterCreate = 0
  mocks.listJobRoles.mockImplementation(async () => {
    if (created) listCallsAfterCreate += 1
    return roles
  })
  mocks.createJobRole.mockImplementation(async (payload: any) => {
    created = true
    roles = [
      {
        id: 'role-1',
        name: payload.name,
        description: payload.description,
        required_skills: payload.required_skills,
        seniority_level: payload.seniority_level,
        status: 'pending_certification'
      }
    ]
    return {}
  })

  render(<GenesisConsole />)

  fireEvent.change(screen.getByPlaceholderText('Job role name'), { target: { value: 'Backend Engineer' } })
  fireEvent.change(screen.getByPlaceholderText('What this role does'), { target: { value: 'Build APIs' } })

  await screen.findByText(/python \(certified\)/i)
  fireEvent.click(screen.getByText(/python \(certified\)/i))
  fireEvent.click(screen.getByRole('button', { name: 'Create Role' }))

  await waitFor(() => {
    expect(mocks.createJobRole).toHaveBeenCalledWith({
      name: 'Backend Engineer',
      description: 'Build APIs',
      required_skills: ['skill-1'],
      seniority_level: 'mid'
    })
  })

  await waitFor(() => {
    expect(listCallsAfterCreate).toBeGreaterThan(0)
  })

  await waitFor(() => {
    expect(screen.getByText('Backend Engineer')).toBeInTheDocument()
  })
})
