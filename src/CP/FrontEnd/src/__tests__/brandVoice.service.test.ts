import { beforeEach, describe, expect, it, vi } from 'vitest'

describe('brandVoice.service', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
  })

  it('gets brand voice from the CP backend route', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue({
      tone_keywords: ['confident'],
      vocabulary_preferences: [],
      messaging_patterns: [],
      example_phrases: ['Let us grow together'],
      voice_description: 'Confident and warm',
    })

    const service = await import('../services/brandVoice.service')
    const result = await service.getBrandVoice()

    expect(spy).toHaveBeenCalledWith('/cp/brand-voice', { method: 'GET' })
    expect(result.voice_description).toBe('Confident and warm')
  })

  it('updates brand voice with PUT payload', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue({
      tone_keywords: ['confident'],
      vocabulary_preferences: [],
      messaging_patterns: [],
      example_phrases: ['Let us grow together'],
      voice_description: 'Confident and warm',
    })

    const service = await import('../services/brandVoice.service')
    await service.updateBrandVoice({ voice_description: 'Confident and warm' })

    expect(spy).toHaveBeenCalledWith(
      '/cp/brand-voice',
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify({ voice_description: 'Confident and warm' }),
      })
    )
  })
