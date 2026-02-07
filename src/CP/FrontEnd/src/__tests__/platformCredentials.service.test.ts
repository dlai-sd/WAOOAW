import { describe, it, expect, vi } from 'vitest'

describe('platformCredentials.service', () => {
  it('calls CP platform credentials endpoints', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue([])

    const svc = await import('../services/platformCredentials.service')
    await svc.listPlatformCredentials()

    expect(spy).toHaveBeenCalledWith('/cp/platform-credentials')
  })
})
