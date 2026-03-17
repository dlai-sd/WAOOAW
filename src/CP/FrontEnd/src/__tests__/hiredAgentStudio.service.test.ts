import { beforeEach, describe, expect, it, vi } from 'vitest'

describe('hiredAgentStudio.service', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
  })

  it('calls the hired-agent studio snapshot endpoint', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue({
      hired_instance_id: 'HAI-123',
      current_step: 'connection',
    })

    const svc = await import('../services/hiredAgentStudio.service')
    const result = await svc.getHiredAgentStudio('HAI-123')

    expect(spy).toHaveBeenCalledWith('/cp/hired-agents/HAI-123/studio')
    expect(result.hired_instance_id).toBe('HAI-123')
  })

  it('PATCHes the hired-agent studio update payload', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue({
      hired_instance_id: 'HAI-123',
      current_step: 'review',
    })

    const svc = await import('../services/hiredAgentStudio.service')
    await svc.updateHiredAgentStudio('HAI-123', {
      identity: { nickname: 'Pipeline Pilot', theme: 'dark' },
      review: { finalize: true, goals_completed: true },
    })

    expect(spy).toHaveBeenCalledWith(
      '/cp/hired-agents/HAI-123/studio',
      expect.objectContaining({
        method: 'PATCH',
        body: JSON.stringify({
          identity: { nickname: 'Pipeline Pilot', theme: 'dark' },
          review: { finalize: true, goals_completed: true },
        }),
      })
    )
  })

  it('URL-encodes hired_instance_id when requesting studio state', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue({
      hired_instance_id: 'HAI/123',
      current_step: 'identity',
    })

    const svc = await import('../services/hiredAgentStudio.service')
    await svc.getHiredAgentStudio('HAI/123')

    expect(spy).toHaveBeenCalledWith('/cp/hired-agents/HAI%2F123/studio')
  })
})