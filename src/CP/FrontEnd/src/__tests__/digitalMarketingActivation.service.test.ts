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

describe('marketingReview.service — draft create and execute', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
  })

  it('createDraftBatch POSTs to /cp/marketing/draft-batches with youtube fields', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue({
      batch_id: 'b-new',
      agent_id: 'AGT-MKT-DMA-001',
      customer_id: 'user-1',
      theme: 'YouTube health tips',
      brand_name: 'Care Clinic',
      created_at: '2026-01-01T00:00:00Z',
      status: 'pending_review',
      posts: [],
    })

    const svc = await import('../services/marketingReview.service')
    const result = await svc.createDraftBatch({
      agent_id: 'AGT-MKT-DMA-001',
      theme: 'YouTube health tips',
      brand_name: 'Care Clinic',
      youtube_credential_ref: 'projects/waooaw-oauth/secrets/hired-1-youtube/versions/latest',
      youtube_visibility: 'private',
      public_release_requested: false,
      requested_artifacts: [{ artifact_type: 'table', prompt: 'Create a weekly content table' }],
    })

    expect(spy).toHaveBeenCalledWith(
      '/cp/marketing/draft-batches',
      expect.objectContaining({
        method: 'POST',
        body: expect.stringContaining('requested_artifacts'),
      })
    )
    expect(result.batch_id).toBe('b-new')
  })

  it('executeDraftPost POSTs to /cp/marketing/draft-posts/execute', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue({
      allowed: true,
      decision_id: 'dec-1',
      post_id: 'post-yt-1',
      execution_status: 'posted',
      provider_post_id: 'yt-abc123',
      provider_post_url: 'https://www.youtube.com/post/yt-abc123',
    })

    const svc = await import('../services/marketingReview.service')
    const result = await svc.executeDraftPost({
      post_id: 'post-yt-1',
      agent_id: 'AGT-MKT-DMA-001',
      approval_id: 'APR-123',
      intent_action: 'publish',
    })

    expect(spy).toHaveBeenCalledWith(
      '/cp/marketing/draft-posts/execute',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          post_id: 'post-yt-1',
          agent_id: 'AGT-MKT-DMA-001',
          approval_id: 'APR-123',
          intent_action: 'publish',
        }),
      })
    )
    expect(result.allowed).toBe(true)
    expect(result.provider_post_url).toBe('https://www.youtube.com/post/yt-abc123')
  })
})
