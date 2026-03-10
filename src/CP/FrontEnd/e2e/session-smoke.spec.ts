import { expect, test } from '@playwright/test'

const e2eSecret = process.env.E2E_SHARED_SECRET

type CpSessionResponse = {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

async function bootstrapCpSession(request: Parameters<typeof test>[0]['request']): Promise<CpSessionResponse> {
  if (!e2eSecret) {
    throw new Error('E2E_SHARED_SECRET is required for CP smoke tests')
  }

  const response = await request.post('/api/auth/e2e/session', {
    headers: {
      'Content-Type': 'application/json',
      'X-E2E-Secret': e2eSecret,
    },
    data: {
      email: 'smoke.cp@waooaw.com',
      name: 'CP Smoke User',
      user_id: 'cp-smoke-user',
    },
  })

  expect(response.ok()).toBeTruthy()
  return response.json()
}

test.describe('CP session smoke', () => {
  test('redirects guests from protected routes to sign-in', async ({ page }) => {
    await page.goto('/discover')
    await page.waitForURL(/\/signin/)
    await expect(page.getByTestId('cp-signin-page')).toBeVisible()
  })

  test.skip(!e2eSecret, 'Requires E2E_SHARED_SECRET')
  test('boots into portal, navigates discover, and signs out', async ({ page, request }) => {
    const session = await bootstrapCpSession(request)

    await page.goto(`/auth/callback?access_token=${encodeURIComponent(session.access_token)}&expires_in=${session.expires_in}`)
    await page.waitForURL(/\/portal/)

    await expect(page.getByTestId('cp-portal-root')).toBeVisible()
    await page.getByTestId('cp-nav-discover').click()
    await expect(page.getByTestId('cp-discover-page')).toBeVisible()
    await expect(page.getByTestId('cp-discover-search-button')).toBeVisible()

    await page.getByTestId('cp-signout-button').click()
    await expect(page.getByRole('button', { name: 'Sign In' })).toBeVisible()
  })
})