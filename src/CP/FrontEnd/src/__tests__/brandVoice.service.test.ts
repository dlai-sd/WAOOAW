import { beforeEach, describe, expect, it, vi } from 'vitest'

describe('brandVoice.service', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
  })

  it('loads brand voice from the CP route', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue({
      tone_keywords: ['warm'],
      vocabulary_preferences: [],
      messaging_patterns: [],
      example_phrases: [],
      voice_description: 'Warm and clear',
    })

    const svc = await import('../services/brandVoice.service')
    const result = await svc.getBrandVoice()

    expect(spy).toHaveBeenCalledWith('/cp/brand-voice', { method: 'GET' })
    expect(result.voice_description).toBe('Warm and clear')
  })

  it('updates brand voice through the CP route', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue({
      tone_keywords: ['warm'],
      vocabulary_preferences: [],
      messaging_patterns: [],
      example_phrases: ['You can trust us.'],
      voice_description: 'Warm and clear',
    })

    const svc = await import('../services/brandVoice.service')
    await svc.updateBrandVoice({
      tone_keywords: ['warm'],
      voice_description: 'Warm and clear',
    })

    expect(spy).toHaveBeenCalledWith(
      '/cp/brand-voice',
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify({
          tone_keywords: ['warm'],
          voice_description: 'Warm and clear',
        }),
      })
    )
  })
