import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { expect, test, vi } from 'vitest'

import GenesisConsole from './GenesisConsole'

const mocks = vi.hoisted(() => {
  return {
    listSkills: vi.fn(async () => []),
    listJobRoles: vi.fn(async () => []),
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
        certifySkill: mocks.certifySkill,
        certifyJobRole: mocks.certifyJobRole
      }
    }
  })
})

test('GenesisConsole renders empty state for skills and job roles', async () => {
  render(<GenesisConsole />)

  await waitFor(() => {
    expect(mocks.listSkills).toHaveBeenCalledTimes(1)
    expect(mocks.listJobRoles).toHaveBeenCalledTimes(1)
  })

  expect(screen.getByText('No skills returned from Plant.')).toBeInTheDocument()
  expect(screen.getByText('No job roles returned from Plant.')).toBeInTheDocument()
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
