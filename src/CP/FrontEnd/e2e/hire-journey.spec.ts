import { expect, test } from '@playwright/test'

const agentId = 'AGT-MKT-HEALTH-001'
const jobRoleId = 'ROLE-MKT-HEALTH-001'
const skillIds = ['SKILL-CONTENT-001', 'SKILL-SOCIAL-001']
const subscriptionId = 'SUB-CP-HIRE-001'
const orderId = 'ORDER-CP-HIRE-001'
const hiredInstanceId = 'HIRED-CP-HIRE-001'

function createJwt(userId: string): string {
  const header = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64url')
  const payload = Buffer.from(
    JSON.stringify({
      user_id: userId,
      email: 'journey.customer@waooaw.com',
      token_type: 'access',
      exp: Math.floor(Date.now() / 1000) + 60 * 60,
      iat: Math.floor(Date.now() / 1000),
    })
  ).toString('base64url')
  return `${header}.${payload}.signature`
}

test.describe('CP hire journey', () => {
  test('moves from discovery to receipt, setup, and truthful post-activation landing', async ({ page }) => {
    const accessToken = createJwt('cp-hire-journey-user')

    await page.route('**/api/**', async (route) => {
      const request = route.request()
      const url = new URL(request.url())
      const path = url.pathname
      const method = request.method()

      if (path.endsWith('/api/auth/refresh')) {
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'No refresh session' }),
        })
        return
      }

      if (path.endsWith('/api/auth/me')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'cp-hire-journey-user',
            email: 'journey.customer@waooaw.com',
            name: 'Journey Customer',
            provider: 'google',
            created_at: '2026-03-10T09:00:00Z',
          }),
        })
        return
      }

      if (path.endsWith('/api/cp/payments/config')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ mode: 'coupon', coupon_code: 'WAOOAW100', coupon_unlimited: true }),
        })
        return
      }

      if (path.endsWith('/api/v1/agents')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: agentId,
              name: 'Healthcare Growth Copilot',
              description: 'Builds compliant growth campaigns for clinics and care brands.',
              job_role_id: jobRoleId,
              industry: 'marketing',
              entity_type: 'agent',
              status: 'active',
              created_at: '2026-03-01T09:00:00Z',
              trial_days: 7,
              allowed_durations: ['monthly'],
              price: 12000,
            },
          ]),
        })
        return
      }

      if (path.endsWith(`/api/v1/agents/${agentId}`)) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: agentId,
            name: 'Healthcare Growth Copilot',
            description: 'Builds compliant growth campaigns for clinics and care brands.',
            job_role_id: jobRoleId,
            industry: 'marketing',
            entity_type: 'agent',
            status: 'active',
            created_at: '2026-03-01T09:00:00Z',
            trial_days: 7,
            allowed_durations: ['monthly'],
            price: 12000,
          }),
        })
        return
      }

      if (path.endsWith(`/api/v1/genesis/job-roles/${jobRoleId}`)) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: jobRoleId,
            name: 'Healthcare Growth Strategist',
            description: 'Designs and operates patient acquisition campaigns.',
            required_skills: skillIds,
            seniority_level: 'senior',
            entity_type: 'job_role',
            status: 'certified',
            created_at: '2026-03-01T09:00:00Z',
          }),
        })
        return
      }

      if (path.endsWith(`/api/v1/genesis/skills/${skillIds[0]}`)) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: skillIds[0],
            name: 'Healthcare Content Ops',
            description: 'Creates compliant campaign content.',
            category: 'domain_expertise',
            entity_type: 'skill',
            status: 'certified',
            created_at: '2026-03-01T09:00:00Z',
          }),
        })
        return
      }

      if (path.endsWith(`/api/v1/genesis/skills/${skillIds[1]}`)) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: skillIds[1],
            name: 'Social Publishing',
            description: 'Schedules and publishes channel content.',
            category: 'technical',
            entity_type: 'skill',
            status: 'certified',
            created_at: '2026-03-01T09:00:00Z',
          }),
        })
        return
      }

      if (path.endsWith('/api/cp/payments/coupon/checkout') && method === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            order_id: orderId,
            payment_provider: 'coupon',
            amount: 0,
            currency: 'INR',
            coupon_code: 'WAOOAW100',
            agent_id: agentId,
            duration: 'monthly',
            subscription_status: 'trialing',
            trial_status: 'active',
            subscription_id: subscriptionId,
          }),
        })
        return
      }

      if (path.endsWith(`/api/cp/hire/wizard/by-subscription/${subscriptionId}`)) {
        await route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Draft not found' }),
        })
        return
      }

      if (path.endsWith('/api/cp/platform-credentials') && method === 'PUT') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ credential_ref: 'cred-instagram-001' }),
        })
        return
      }

      if (path.endsWith('/api/cp/hire/wizard/draft') && method === 'PUT') {
        const body = request.postDataJSON() as Record<string, unknown>
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            hired_instance_id: hiredInstanceId,
            subscription_id: body.subscription_id,
            agent_id: body.agent_id,
            nickname: body.nickname || 'Clinic Growth Desk',
            theme: body.theme || 'default',
            config: body.config || {},
            configured: true,
            goals_completed: false,
            subscription_status: 'trialing',
            trial_status: 'active',
            trial_start_at: '2026-03-10T09:00:00Z',
            trial_end_at: '2026-03-17T09:00:00Z',
          }),
        })
        return
      }

      if (path.endsWith('/api/cp/hire/wizard/finalize') && method === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            hired_instance_id: hiredInstanceId,
            subscription_id: subscriptionId,
            agent_id: agentId,
            nickname: 'Clinic Growth Desk',
            theme: 'dark',
            config: {
              platforms: [
                {
                  platform: 'instagram',
                  credential_ref: 'cred-instagram-001',
                  posting_identity: 'DrSharmaClinic',
                },
              ],
            },
            configured: true,
            goals_completed: true,
            subscription_status: 'trialing',
            trial_status: 'active',
            trial_start_at: '2026-03-10T09:00:00Z',
            trial_end_at: '2026-03-17T09:00:00Z',
          }),
        })
        return
      }

      if (path.endsWith('/api/cp/my-agents/summary')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            instances: [
              {
                subscription_id: subscriptionId,
                agent_id: agentId,
                duration: 'monthly',
                status: 'active',
                current_period_start: '2026-03-10T09:00:00Z',
                current_period_end: '2026-04-10T09:00:00Z',
                cancel_at_period_end: false,
                hired_instance_id: hiredInstanceId,
                agent_type_id: 'marketing.digital_marketing.v1',
                nickname: 'Clinic Growth Desk',
                configured: true,
                goals_completed: true,
                trial_status: 'active',
                trial_start_at: '2026-03-10T09:00:00Z',
                trial_end_at: '2026-03-17T09:00:00Z',
                subscription_status: 'trialing',
              },
            ],
          }),
        })
        return
      }

      if (path.endsWith(`/api/cp/hired-agents/by-subscription/${subscriptionId}`)) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            hired_instance_id: hiredInstanceId,
            subscription_id: subscriptionId,
            agent_id: agentId,
            agent_type_id: 'marketing.digital_marketing.v1',
            nickname: 'Clinic Growth Desk',
            theme: 'dark',
            config: {
              platforms: [
                {
                  platform: 'instagram',
                  credential_ref: 'cred-instagram-001',
                  posting_identity: 'DrSharmaClinic',
                },
              ],
            },
            configured: true,
            goals_completed: true,
            trial_status: 'active',
          }),
        })
        return
      }

      if (path.endsWith('/api/v1/agent-types/marketing.digital_marketing.v1')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            agent_type_id: 'marketing.digital_marketing.v1',
            version: 'v1',
            config_schema: {
              fields: [
                { key: 'platforms', label: 'Platforms', type: 'list', required: false },
              ],
            },
            goal_templates: [],
            enforcement_defaults: { approval_required: true, deterministic: false },
          }),
        })
        return
      }

      if (path.includes(`/api/cp/hired-agents/${hiredInstanceId}/goals`)) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ hired_instance_id: hiredInstanceId, goals: [] }),
        })
        return
      }

      if (path.includes(`/api/cp/hired-agents/${hiredInstanceId}/deliverables`)) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ hired_instance_id: hiredInstanceId, deliverables: [] }),
        })
        return
      }

      if (path.includes(`/api/cp/hired-agents/${hiredInstanceId}/performance-stats`)) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([]),
        })
        return
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({}),
      })
    })

    await page.goto(`/auth/callback?access_token=${encodeURIComponent(accessToken)}&expires_in=3600`)
    await page.waitForURL(/\/portal/)
    await expect(page.getByTestId('cp-portal-root')).toBeVisible()

    await page.getByTestId('cp-nav-discover').click()
    await expect(page.getByTestId('cp-discover-page')).toBeVisible()
    await page.getByTestId('cp-discover-search-input').fill('Healthcare')
    await page.getByTestId('cp-discover-search-button').click()

    await expect(page.getByTestId(`cp-agent-card-${agentId}`)).toBeVisible()
    await page.getByTestId(`cp-agent-card-cta-${agentId}`).click()

    await expect(page.getByTestId('cp-agent-detail-page')).toBeVisible()
    await page.getByTestId('cp-agent-detail-start-trial').click()

    await expect(page.getByTestId('cp-booking-modal')).toBeVisible()
    await page.getByTestId('cp-booking-full-name').fill('Asha Sharma')
    await page.getByTestId('cp-booking-email').fill('asha@clinicgrowth.com')
    await page.getByTestId('cp-booking-company').fill('Clinic Growth Studio')
    await page.getByTestId('cp-booking-phone').fill('+91 98765 43210')
    await page.getByTestId('cp-booking-coupon-code').fill('WAOOAW100')
    await page.getByTestId('cp-booking-submit').click()

    await page.waitForURL(new RegExp(`/hire/receipt/${orderId}`))
    await expect(page.getByTestId('cp-hire-receipt-page')).toBeVisible()
    await page.getByTestId('cp-hire-receipt-continue').click()

    await page.waitForURL(new RegExp(`/hire/setup/${subscriptionId}`))
    await expect(page.getByTestId('cp-hire-setup-page')).toBeVisible()
    await expect(page.getByTestId('cp-hire-setup-step-1')).toBeVisible()

    await page.getByTestId('cp-hire-setup-nickname').fill('Clinic Growth Desk')
    await page.getByTestId('cp-hire-setup-next').click()
    await expect(page.getByTestId('cp-hire-setup-step-2')).toBeVisible()

    await page.getByTestId('cp-hire-setup-theme').selectOption('dark')
    await page.getByTestId('cp-hire-setup-next').click()
    await expect(page.getByTestId('cp-hire-setup-step-3')).toBeVisible()

    await page.getByTestId('cp-hire-setup-platform').selectOption('instagram')
    await page.getByTestId('cp-hire-setup-posting-identity').fill('DrSharmaClinic')
    await page.getByTestId('cp-hire-setup-access-token').fill('token-123')
    await page.getByTestId('cp-hire-setup-refresh-token').fill('refresh-123')
    await page.getByTestId('cp-hire-setup-next').click()
    await expect(page.getByTestId('cp-hire-setup-step-4')).toBeVisible()

    await page.getByTestId('cp-hire-setup-goals-completed').click()
    await page.getByTestId('cp-hire-setup-activate').click()

    await page.waitForURL(/\/portal/)
    await expect(page.getByTestId('cp-portal-entry-banner')).toBeVisible()
    await expect(page.getByText(`${agentId} is now in runtime setup`)).toBeVisible()
    await expect(page.getByText('You landed in My Agents because that is the first truthful place to confirm the runtime, monitor hydration, and continue operating without guessing.')).toBeVisible()
  })
})