import { expect, test } from '@playwright/test'

const e2eSecret = process.env.E2E_SHARED_SECRET

type PpTokenResponse = {
  access_token: string
  token_type: string
  expires_in: number
  user: {
    id: string
    email: string
    roles: string[]
  }
}

async function bootstrapPpSession(request: Parameters<typeof test>[0]['request']): Promise<PpTokenResponse> {
  if (!e2eSecret) {
    throw new Error('E2E_SHARED_SECRET is required for PP smoke tests')
  }

  const response = await request.post('/api/auth/e2e/admin-token', {
    headers: {
      'Content-Type': 'application/json',
      'X-E2E-Secret': e2eSecret,
    },
    data: {
      email: 'smoke.admin@waooaw.com',
      user_id: 'pp-smoke-admin',
      roles: ['admin'],
    },
  })

  expect(response.ok()).toBeTruthy()
  return response.json()
}

test.describe('PP session smoke', () => {
  test('shows the public landing shell for guests', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByTestId('pp-public-shell')).toBeVisible()
    await expect(page.getByTestId('pp-signin-trigger')).toBeVisible()
  })

  test.skip(!e2eSecret, 'Requires E2E_SHARED_SECRET')
  test('boots with an injected admin token and logs out cleanly', async ({ page, request }) => {
    const session = await bootstrapPpSession(request)

    await page.addInitScript((accessToken: string) => {
      window.localStorage.setItem('pp_access_token', accessToken)
    }, session.access_token)

    await page.goto('/')
    await expect(page.getByTestId('pp-dashboard-page')).toBeVisible()

    await page.getByTestId('pp-logout-button').click()
    await expect(page.getByTestId('pp-public-shell')).toBeVisible()
  })
})