import { describe, expect, it, vi } from 'vitest'

vi.mock('../services/gatewayApiClient', () => ({
  gatewayRequestJson: vi.fn(),
}))

import { gatewayRequestJson } from '../services/gatewayApiClient'
import {
  getDigitalMarketingActivationWorkspace,
  getNextPendingPlatform,
  getPlatformPreparationState,
  patchDigitalMarketingActivationWorkspace,
} from '../services/digitalMarketingActivation.service'

describe('digitalMarketingActivation.service', () => {
  it('hits the expected CP route for workspace GET', async () => {
    vi.mocked(gatewayRequestJson).mockResolvedValueOnce({ hired_instance_id: 'HAI-1' } as any)

    await getDigitalMarketingActivationWorkspace('HAI-1')

    expect(gatewayRequestJson).toHaveBeenCalledWith('/cp/digital-marketing-activation/HAI-1')
  })

  it('sends only the partial workspace patch body for PATCH', async () => {
    vi.mocked(gatewayRequestJson).mockResolvedValueOnce({ hired_instance_id: 'HAI-1' } as any)

    await patchDigitalMarketingActivationWorkspace('HAI-1', {
      help_visible: true,
      induction: { brand_name: 'WAOOAW' },
    })

    expect(gatewayRequestJson).toHaveBeenCalledWith(
      '/cp/digital-marketing-activation/HAI-1',
      expect.objectContaining({
        method: 'PATCH',
        body: JSON.stringify({
          help_visible: true,
          induction: { brand_name: 'WAOOAW' },
        }),
      })
    )
  })

  it('returns the next selected platform that is not yet complete', () => {
    expect(
      getNextPendingPlatform(
        ['youtube', 'instagram'],
        [
          { platform_key: 'youtube', complete: true },
          { platform_key: 'instagram', complete: false },
        ]
      )
    ).toBe('instagram')
  })

  it('treats a connected platform as ready only when the workspace marks the step complete', () => {
    expect(
      getPlatformPreparationState(
        'youtube',
        {
          hired_instance_id: 'HAI-1',
          help_visible: false,
          activation_complete: false,
          induction: {
            nickname: '',
            theme: 'default',
            primary_language: 'en',
            timezone: '',
            brand_name: '',
            offerings_services: [],
            location: '',
            target_audience: '',
            notes: '',
          },
          prepare_agent: {
            selected_platforms: ['youtube'],
            platform_steps: [{ platform_key: 'youtube', complete: false }],
            all_selected_platforms_completed: false,
          },
          campaign_setup: {
            master_theme: '',
            derived_themes: [],
            schedule: { start_date: '', posts_per_week: 0, preferred_days: [], preferred_hours_utc: [] },
          },
          updated_at: '2026-03-18T09:00:00Z',
        } as any,
        [{ id: 'CONN-1', hired_instance_id: 'HAI-1', skill_id: 'default', platform_key: 'youtube', created_at: '', updated_at: '' }]
      ).ready
    ).toBe(false)
  })
})
