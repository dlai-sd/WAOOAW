import { gatewayRequestJson } from './gatewayApiClient'

export interface BrandVoiceData {
  tone_keywords: string[]
  vocabulary_preferences: string[]
  messaging_patterns: string[]
  example_phrases: string[]
  voice_description: string
}

export async function getBrandVoice(): Promise<BrandVoiceData> {
  return gatewayRequestJson<BrandVoiceData>('/cp/brand-voice', { method: 'GET' })
}

export async function updateBrandVoice(data: Partial<BrandVoiceData>): Promise<BrandVoiceData> {
  return gatewayRequestJson<BrandVoiceData>('/cp/brand-voice', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
}
