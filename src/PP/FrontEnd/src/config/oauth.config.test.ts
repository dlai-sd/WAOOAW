import { beforeEach, describe, expect, test } from 'vitest'

import { API_ENDPOINTS, config } from './oauth.config'

describe('oauth.config runtime hydration', () => {
  beforeEach(() => {
    delete (window as any).__WAOOAW_PP_RUNTIME_CONFIG__
  })

  test('reads runtime config even when it appears after module import', () => {
    expect(config.googleClientId).toBe('')

    ;(window as any).__WAOOAW_PP_RUNTIME_CONFIG__ = {
      environment: 'demo',
      apiBaseUrl: 'https://pp.demo.waooaw.com/api',
      googleClientId: 'demo-google-client-id'
    }

    expect(config.name).toBe('demo')
    expect(config.googleClientId).toBe('demo-google-client-id')
    expect(API_ENDPOINTS.googleVerify).toBe('https://pp.demo.waooaw.com/api/auth/google/verify')
  })
})