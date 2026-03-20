import { expect, test } from '@playwright/test'

const hiredInstanceId = 'HAI-DMA-1'
const subscriptionId = 'SUB-DMA-1'

function createJwt(userId: string): string {
  const header = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64url')
  const payload = Buffer.from(
    JSON.stringify({
      user_id: userId,
      email: 'customer@waooaw.com',
      token_type: 'access',
      exp: Math.floor(Date.now() / 1000) + 60 * 60,
      iat: Math.floor(Date.now() / 1000),
    })
  ).toString('base64url')

  return `${header}.${payload}.signature`
}

test.describe('Digital Marketing activation wizard', () => {
  test('covers the full wizard path through runtime-ready confirmation with mocked APIs', async ({ page }) => {
    const accessToken = createJwt('cp-dma-user')
    const summaryInstance = {
      subscription_id: subscriptionId,
      agent_id: 'AGT-MKT-DMA-001',
      agent_type_id: 'marketing.digital_marketing.v1',
      duration: 'monthly',
      status: 'active',
      current_period_start: '2026-03-01T00:00:00Z',
      current_period_end: '2026-04-01T00:00:00Z',
      cancel_at_period_end: false,
      hired_instance_id: hiredInstanceId,
      nickname: 'Growth Copilot',
      configured: true,
      goals_completed: false,
      trial_status: 'active',
      trial_end_at: '2026-04-01T00:00:00Z',
    }

    const activation = {
      hired_instance_id: hiredInstanceId,
      customer_id: 'CUST-DMA-1',
      agent_type_id: 'marketing.digital_marketing.v1',
      workspace: {
        help_visible: false,
        activation_complete: false,
        brand_name: 'WAOOAW',
        location: 'Pune',
        primary_language: 'en',
        timezone: 'Asia/Kolkata',
        business_context: 'B2B marketplace for specialised AI agents.',
        offerings_services: ['Marketplace activation', 'Campaign management'],
        platforms_enabled: ['youtube', 'instagram'],
        platform_bindings: {
          youtube: { skill_id: 'default', connected: true, credential_ref: 'cred-youtube-1' },
          instagram: { skill_id: 'default', connected: true, credential_ref: 'cred-instagram-1' },
        },
        campaign_setup: {
          campaign_id: 'CAM-DMA-1',
          master_theme: '',
          derived_themes: [],
          schedule: {
            start_date: '',
            posts_per_week: 0,
            preferred_days: [],
            preferred_hours_utc: [],
          },
        },
      },
      readiness: {
        brief_complete: true,
        youtube_selected: true,
        youtube_connection_ready: true,
        configured: true,
        can_finalize: true,
        missing_requirements: [],
      },
      updated_at: '2026-03-18T09:00:00Z',
    }

    await page.route('**/api/**', async (route) => {
      const request = route.request()
      const { pathname } = new URL(request.url())
      const method = request.method()

      if (pathname.endsWith('/api/auth/refresh')) {
        await route.fulfill({ status: 401, contentType: 'application/json', body: JSON.stringify({ detail: 'No refresh session' }) })
        return
      }

      if (pathname.endsWith('/api/auth/me')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'cp-dma-user',
            email: 'customer@waooaw.com',
            name: 'DMA Customer',
            provider: 'google',
            created_at: '2026-03-10T09:00:00Z',
          }),
        })
        return
      }

      if (pathname.endsWith('/api/auth/logout')) {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true }) })
        return
      }

      if (pathname.endsWith('/api/cp/payments/config')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ mode: 'coupon', coupon_code: 'WAOOAW100', coupon_unlimited: true }),
        })
        return
      }

      if (pathname.endsWith('/api/cp/my-agents/summary')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ instances: [summaryInstance] }),
        })
        return
      }

      if (pathname.endsWith(`/api/cp/hired-agents/${hiredInstanceId}/deliverables`)) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ hired_instance_id: hiredInstanceId, deliverables: [] }),
        })
        return
      }

      if (pathname.endsWith(`/api/cp/hired-agents/${hiredInstanceId}/platform-connections`) && method === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: 'conn-youtube-1',
              hired_instance_id: hiredInstanceId,
              skill_id: 'default',
              platform_key: 'youtube',
              status: 'connected',
              connected_at: '2026-03-18T09:00:00Z',
              last_verified_at: '2026-03-18T09:00:00Z',
              created_at: '2026-03-18T09:00:00Z',
              updated_at: '2026-03-18T09:00:00Z',
            },
            {
              id: 'conn-instagram-1',
              hired_instance_id: hiredInstanceId,
              skill_id: 'default',
              platform_key: 'instagram',
              status: 'connected',
              connected_at: '2026-03-18T09:00:00Z',
              last_verified_at: '2026-03-18T09:00:00Z',
              created_at: '2026-03-18T09:00:00Z',
              updated_at: '2026-03-18T09:00:00Z',
            },
          ]),
        })
        return
      }

      if (pathname.endsWith(`/api/cp/digital-marketing-activation/${hiredInstanceId}`) && method === 'GET') {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(activation) })
        return
      }

      if (pathname.endsWith(`/api/cp/digital-marketing-activation/${hiredInstanceId}`) && method === 'PUT') {
        const body = request.postDataJSON() as { workspace?: Record<string, any> }
        activation.workspace = {
          ...activation.workspace,
          ...(body.workspace || {}),
          campaign_setup: {
            ...activation.workspace.campaign_setup,
            ...(body.workspace?.campaign_setup || {}),
            schedule: {
              ...activation.workspace.campaign_setup.schedule,
              ...(body.workspace?.campaign_setup?.schedule || {}),
            },
          },
        }

        if (body.workspace?.activation_complete) {
          activation.workspace.activation_complete = true
          summaryInstance.configured = true
          summaryInstance.goals_completed = true
        }

        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(activation) })
        return
      }

      if (pathname.endsWith(`/api/cp/digital-marketing-activation/${hiredInstanceId}/generate-theme-plan`) && method === 'POST') {
        const body = request.postDataJSON() as { campaign_setup?: { schedule?: Record<string, any> } }
        activation.workspace.campaign_setup = {
          ...activation.workspace.campaign_setup,
          master_theme: 'Trust-first growth',
          derived_themes: [
            { title: 'Proof', description: 'Show results and customer proof.', frequency: 'weekly' },
            { title: 'Education', description: 'Teach the market why the workflow works.', frequency: 'weekly' },
          ],
          schedule: {
            ...activation.workspace.campaign_setup.schedule,
            ...(body.campaign_setup?.schedule || {}),
          },
        }

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            campaign_id: activation.workspace.campaign_setup.campaign_id,
            master_theme: activation.workspace.campaign_setup.master_theme,
            derived_themes: activation.workspace.campaign_setup.derived_themes,
            workspace: activation,
          }),
        })
        return
      }

      if (pathname.endsWith(`/api/cp/digital-marketing-activation/${hiredInstanceId}/theme-plan`) && method === 'PATCH') {
        const body = request.postDataJSON() as {
          master_theme?: string
          derived_themes?: Array<Record<string, any>>
          campaign_setup?: { schedule?: Record<string, any> }
        }
        activation.workspace.campaign_setup = {
          ...activation.workspace.campaign_setup,
          master_theme: body.master_theme || activation.workspace.campaign_setup.master_theme,
          derived_themes: body.derived_themes || activation.workspace.campaign_setup.derived_themes,
          schedule: {
            ...activation.workspace.campaign_setup.schedule,
            ...(body.campaign_setup?.schedule || {}),
          },
        }

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            campaign_id: activation.workspace.campaign_setup.campaign_id,
            master_theme: activation.workspace.campaign_setup.master_theme,
            derived_themes: activation.workspace.campaign_setup.derived_themes,
            workspace: activation,
          }),
        })
        return
      }

      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) })
    })

    await page.goto(`/auth/callback?access_token=${encodeURIComponent(accessToken)}&expires_in=3600`)
    await page.waitForURL(/\/portal/)
    await expect(page.getByTestId('cp-portal-root')).toBeVisible()

    await page.getByTestId('cp-nav-my-agents').click()
    await expect(page.getByText('My Agents (1)')).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Digital Marketing activation' })).toBeVisible()

    const wizardHelpToggle = page.getByRole('button', { name: 'Show Help' })
    await page.getByRole('button', { name: 'Master Theme' }).click()
    await wizardHelpToggle.click()
    await expect(page.getByTestId('dma-help-panel-primary')).toBeVisible()
    await expect(page.getByTestId('dma-help-panel-secondary')).toBeVisible()
    await page.getByRole('button', { name: 'Hide Help', exact: true }).last().click()

    await page.getByRole('button', { name: 'Generate theme plan' }).click()
    await expect(page.getByLabel('Master theme')).toHaveValue('Trust-first growth')
    await expect(page.getByLabel('Derived theme title 1')).toHaveValue('Proof')
    await expect(page.getByLabel('Derived theme title 2')).toHaveValue('Education')

    await page.getByLabel('Master theme').fill('Trust-first growth for WAOOAW')
    await page.getByRole('button', { name: 'Save theme plan' }).click()
    await expect(page.getByLabel('Master theme')).toHaveValue('Trust-first growth for WAOOAW')

    await page.getByRole('button', { name: 'Confirm Schedule' }).click()
    await expect(page.getByText('Activation summary')).toBeVisible()
    await expect(page.getByText(/Platforms:/)).toContainText('youtube, instagram')
    await expect(page.getByText(/Master theme:/)).toContainText('Trust-first growth for WAOOAW')
    await expect(page.getByText(/Derived themes:/)).toContainText('Proof, Education')

    await page.getByLabel('Start date').fill('2026-03-22')
    await page.getByLabel('Posts per week').fill('3')
    await page.getByLabel('Preferred days').fill('Monday, Wednesday, Friday')
    await page.getByLabel('Preferred hours UTC').fill('9, 17')

    await expect(page.getByRole('button', { name: 'Finish activation' })).toBeEnabled()
    await page.getByRole('button', { name: 'Finish activation' }).click()

    await expect(page.getByText('Runtime-ready')).toBeVisible()
    await expect(page.getByText('This hire has completed setup and is ready for campaign runtime handoff.')).toBeVisible()
  })
})
