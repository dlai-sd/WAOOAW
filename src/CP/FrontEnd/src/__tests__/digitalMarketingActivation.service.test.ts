import { beforeEach, describe, expect, it, vi } from 'vitest'

describe('digitalMarketingActivation.service', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
  })

  it('loads the activation workspace from the CP route', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue({
      hired_instance_id: 'HIRED-1',
      agent_type_id: 'marketing.digital_marketing.v1',
      workspace: { brand_name: 'WAOOAW' },
      readiness: {
        brief_complete: false,
        youtube_selected: false,
        youtube_connection_ready: true,
        configured: false,
        can_finalize: false,
        missing_requirements: ['business_profile'],
      },
      updated_at: '2026-03-19T12:00:00Z',
    })

    const svc = await import('../services/digitalMarketingActivation.service')
    const result = await svc.getDigitalMarketingActivationWorkspace('HIRED/1')

    expect(spy).toHaveBeenCalledWith('/cp/digital-marketing-activation/HIRED%2F1', { method: 'GET' })
    expect(result.workspace.brand_name).toBe('WAOOAW')
  })

  it('saves the activation workspace through the CP route', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue({
      hired_instance_id: 'HIRED-2',
      agent_type_id: 'marketing.digital_marketing.v1',
      workspace: { brand_name: 'WAOOAW', platforms_enabled: ['youtube'] },
      readiness: {
        brief_complete: true,
        youtube_selected: true,
        youtube_connection_ready: false,
        configured: true,
        can_finalize: false,
        missing_requirements: ['youtube_connection'],
      },
      updated_at: '2026-03-19T12:00:00Z',
    })

    const svc = await import('../services/digitalMarketingActivation.service')
    await svc.upsertDigitalMarketingActivationWorkspace('HIRED-2', {
      workspace: {
        brand_name: 'WAOOAW',
        platforms_enabled: ['youtube'],
      },
    })

    expect(spy).toHaveBeenCalledWith(
      '/cp/digital-marketing-activation/HIRED-2',
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify({
          workspace: {
            brand_name: 'WAOOAW',
            platforms_enabled: ['youtube'],
          },
        }),
      })
    )
  })

  it('builds stable platform bindings for selected channels', async () => {
    const svc = await import('../services/digitalMarketingActivation.service')

    expect(
      svc.buildMarketingPlatformBindings(['youtube', 'instagram'], { youtube: { credential_ref: 'cred-yt-1' } }, 'default')
    ).toEqual({
      youtube: { credential_ref: 'cred-yt-1', skill_id: 'default' },
      instagram: { skill_id: 'default' },
    })
  })
})