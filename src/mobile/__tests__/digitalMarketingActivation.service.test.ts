import cpApiClient from '@/lib/cpApiClient'
import {
  getDigitalMarketingActivationWorkspace,
  upsertDigitalMarketingActivationWorkspace,
  patchDigitalMarketingActivationWorkspace,
  generateDigitalMarketingThemePlan,
} from '@/services/digitalMarketingActivation.service'

jest.mock('@/lib/cpApiClient', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    put: jest.fn(),
    patch: jest.fn(),
    post: jest.fn(),
  },
}))

const mockGet = (cpApiClient.get as jest.Mock)
const mockPut = (cpApiClient.put as jest.Mock)
const mockPatch = (cpApiClient.patch as jest.Mock)
const mockPost = (cpApiClient.post as jest.Mock)

const mockWorkspaceResponse = {
  hired_instance_id: 'x',
  agent_type_id: 'marketing.digital_marketing.v1',
  workspace: {},
  readiness: {
    brief_complete: false,
    youtube_selected: false,
    youtube_connection_ready: false,
    configured: false,
    can_finalize: false,
    missing_requirements: [],
  },
  updated_at: '2026-01-01T00:00:00Z',
}

describe('digitalMarketingActivation.service', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('E1-S1-T1: getDigitalMarketingActivationWorkspace resolves with hired_instance_id', async () => {
    mockGet.mockResolvedValueOnce({ data: mockWorkspaceResponse })
    const result = await getDigitalMarketingActivationWorkspace('x')
    expect(result.hired_instance_id).toBe('x')
  })

  it('E1-S1-T2: upsertDigitalMarketingActivationWorkspace calls put with path containing /x', async () => {
    mockPut.mockResolvedValueOnce({ data: mockWorkspaceResponse })
    await upsertDigitalMarketingActivationWorkspace('x', { workspace: {} } as any)
    const callArgs = mockPut.mock.calls[0]
    expect(callArgs[0]).toContain('/x')
  })

  it('E1-S1-T3: generateDigitalMarketingThemePlan calls path ending in /generate-theme-plan', async () => {
    const mockResp = {
      master_theme: 'test',
      derived_themes: [],
      workspace: mockWorkspaceResponse,
    }
    mockPost.mockResolvedValueOnce({ data: mockResp })
    await generateDigitalMarketingThemePlan('x')
    const callArgs = mockPost.mock.calls[0]
    expect(callArgs[0]).toMatch(/\/generate-theme-plan$/)
  })

  it('E1-S1-T4: patchDigitalMarketingActivationWorkspace rejects when cpApiClient.patch rejects', async () => {
    mockPatch.mockRejectedValueOnce(new Error('500'))
    await expect(patchDigitalMarketingActivationWorkspace('x', {})).rejects.toThrow('500')
  })

  it('E1-S1-T5: patchDigitalMarketingActivationWorkspace includes X-Correlation-ID header', async () => {
    mockPatch.mockResolvedValueOnce({ data: mockWorkspaceResponse })
    await patchDigitalMarketingActivationWorkspace('x', {})
    const callArgs = mockPatch.mock.calls[0]
    const headers = (callArgs[2] as { headers?: Record<string, string> })?.headers
    expect(headers).toBeDefined()
    expect(typeof headers!['X-Correlation-ID']).toBe('string')
    expect(headers!['X-Correlation-ID'].length).toBeGreaterThan(0)
  })
})
