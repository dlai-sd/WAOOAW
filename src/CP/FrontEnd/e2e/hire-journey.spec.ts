import { expect, test } from '@playwright/test'

const agentId = 'AGT-MKT-DMA-001'
const jobRoleId = 'ROLE-MKT-DMA-001'
const skillIds = ['SKILL-THEME-DISCOVERY-001', 'SKILL-YOUTUBE-PUBLISH-001']
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
  test('moves from discovery to DMA runtime truth with approval-gated YouTube readiness', async ({ page }) => {
    const accessToken = createJwt('cp-hire-journey-user')

    await page.route('**/api/**', async (route) => {
      const request = route.request()
      const url = new URL(request.url())
      const path = url.pathname
      const method = request.method()

      if (path.endsWith('/api/auth/refresh')) {
        await route.fulfill({ status: 401, contentType: 'application/json', body: JSON.stringify({ detail: 'No refresh session' }) })
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

      if (path.endsWith('/api/cp/catalog/agents')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              release_id: 'CAR-DMA-001',
              id: agentId,
              public_name: 'Digital Marketing Agent',
              short_description: 'Captures Theme Discovery, generates drafts, and keeps YouTube publish gated by exact customer approval.',
              industry_name: 'Marketing',
              job_role_label: 'Digital Marketing Strategist',
              monthly_price_inr: 12000,
              trial_days: 7,
              allowed_durations: ['monthly'],
              supported_channels: ['youtube'],
              approval_mode: 'manual_review',
              agent_type_id: 'marketing.digital_marketing.v1',
              internal_definition_version_id: '1.0.0',
              external_catalog_version: 'v1',
              lifecycle_state: 'live_on_cp',
              approved_for_new_hire: true,
              retired_from_catalog_at: null,
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
            name: 'Digital Marketing Agent',
            description: 'Captures Theme Discovery, generates drafts, and keeps YouTube publish gated by exact customer approval.',
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
            name: 'Digital Marketing Strategist',
            description: 'Owns Theme Discovery, content generation, approvals, and approved YouTube publishing.',
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
            name: 'Theme Discovery',
            description: 'Captures the structured business brief before content generation starts.',
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
            name: 'Approved YouTube Publishing',
            description: 'Publishes only after exact deliverable approval and customer channel readiness exist.',
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
        await route.fulfill({ status: 404, contentType: 'application/json', body: JSON.stringify({ detail: 'Draft not found' }) })
        return
      }

      if (path.endsWith('/api/cp/youtube-connections') && method === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: 'cred-youtube-001',
              customer_id: 'cp-hire-journey-user',
              platform_key: 'youtube',
              display_name: 'Clinic Growth Studio',
              granted_scopes: ['youtube.upload'],
              verification_status: 'verified',
              connection_status: 'connected',
              created_at: '2026-03-10T09:00:00Z',
              updated_at: '2026-03-10T09:00:00Z',
            },
          ]),
        })
        return
      }

      if (path.endsWith('/attach') && path.includes('/api/cp/youtube-connections/') && method === 'POST') {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ attached: true }) })
        return
      }

      if (path.endsWith('/api/cp/platform-credentials') && method === 'PUT') {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ credential_ref: 'cred-youtube-001' }) })
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
            nickname: body.nickname || 'YouTube Growth Desk',
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
            nickname: 'YouTube Growth Desk',
            theme: 'dark',
            config: {
              platforms: [
                {
                  platform: 'youtube',
                  credential_ref: 'cred-youtube-001',
                  posting_identity: 'ClinicGrowthStudio',
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
                nickname: 'YouTube Growth Desk',
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
            nickname: 'YouTube Growth Desk',
            theme: 'dark',
            config: {
              platforms: [
                {
                  platform: 'youtube',
                  credential_ref: 'cred-youtube-001',
                  posting_identity: 'ClinicGrowthStudio',
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

      if (path.endsWith(`/api/cp/hired-agents/${hiredInstanceId}/studio`)) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            hired_instance_id: hiredInstanceId,
            subscription_id: subscriptionId,
            agent_id: agentId,
            agent_type_id: 'marketing.digital_marketing.v1',
            customer_id: 'cp-hire-journey-user',
            mode: 'edit',
            selection_required: false,
            current_step: 'review',
            steps: [
              { key: 'identity', title: 'Identity and voice', complete: true, blocked: false, summary: 'Business-facing name and theme are ready.' },
              { key: 'connection', title: 'Connection', complete: true, blocked: false, summary: 'YouTube connection verified and ready.' },
              { key: 'operating_plan', title: 'Operating plan', complete: true, blocked: false, summary: 'Operating plan is in place.' },
              { key: 'review', title: 'Review edits', complete: true, blocked: false, summary: 'Runtime is ready for review.' },
            ],
            identity: { nickname: 'YouTube Growth Desk', theme: 'dark', complete: true },
            connection: {
              platform_key: 'youtube',
              skill_id: 'default',
              connection_id: null,
              customer_platform_credential_id: 'cred-youtube-001',
              status: 'connected',
              complete: true,
              summary: 'Clinic Growth Studio is connected and verified.',
            },
            operating_plan: {
              complete: true,
              goals_completed: true,
              goal_count: 1,
              skill_config_count: 1,
              summary: 'Theme Discovery and cadence are configured.',
            },
            review: { complete: true, summary: 'Runtime is ready.' },
            configured: true,
            goals_completed: true,
            trial_status: 'active',
            subscription_status: 'trialing',
            updated_at: '2026-03-10T10:00:00Z',
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
            goal_templates: [
              {
                goal_template_id: 'marketing.daily_youtube_short.v1',
                name: 'Daily YouTube short',
                default_frequency: 'three_per_week',
                settings_schema: {
                  fields: [
                    {
                      key: 'platform',
                      label: 'Platform',
                      type: 'enum',
                      required: true,
                      options: ['youtube'],
                    },
                  ],
                },
                skill_binding: 'skill-theme-discovery',
              },
            ],
            enforcement_defaults: { approval_required: true, deterministic: true },
          }),
        })
        return
      }

      if (path.endsWith(`/api/cp/hired-agents/${hiredInstanceId}/goals`)) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            hired_instance_id: hiredInstanceId,
            goals: [
              {
                goal_instance_id: 'GOAL-DMA-1',
                goal_template_id: 'marketing.daily_youtube_short.v1',
                frequency: 'three_per_week',
                settings: { platform: 'youtube' },
              },
            ],
          }),
        })
        return
      }

      if (path.endsWith(`/api/cp/hired-agents/${hiredInstanceId}/skills`)) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              skill_id: 'skill-theme-discovery',
              display_name: 'Theme Discovery',
              goal_schema: {
                fields: [
                  { key: 'business_name', label: 'Business name', required: true },
                  { key: 'brand_voice', label: 'Brand voice', required: true },
                ],
              },
              goal_config: {
                business_name: 'Clinic Growth Studio',
                brand_voice: 'Trusted specialist guidance for busy parents on YouTube.',
              },
            },
          ]),
        })
        return
      }

      if (path.endsWith(`/api/cp/hired-agents/${hiredInstanceId}/platform-connections`)) {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
        return
      }

      if (path.endsWith(`/api/cp/hired-agents/${hiredInstanceId}/deliverables`)) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            hired_instance_id: hiredInstanceId,
            deliverables: [
              {
                deliverable_id: 'DEL-DMA-1',
                hired_instance_id: hiredInstanceId,
                goal_instance_id: 'GOAL-DMA-1',
                goal_template_id: 'marketing.daily_youtube_short.v1',
                title: 'YouTube explainer draft',
                payload: {
                  destination: {
                    destination_type: 'youtube',
                    metadata: {
                      visibility: 'private',
                      public_release_requested: false,
                    },
                  },
                  summary: 'Draft explainer awaiting exact customer approval before publish.',
                },
                review_status: 'pending_review',
                review_notes: null,
                approval_id: null,
                execution_status: 'not_executed',
                created_at: '2026-03-10T10:00:00Z',
                updated_at: '2026-03-10T10:00:00Z',
              },
            ],
          }),
        })
        return
      }

      if (path.endsWith(`/api/cp/hired-agents/${hiredInstanceId}/performance-stats`)) {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
        return
      }

      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) })
    })

    await page.goto(`/auth/callback?access_token=${encodeURIComponent(accessToken)}&expires_in=3600`)
    await page.waitForURL(/\/portal/)
    await expect(page.getByTestId('cp-portal-root')).toBeVisible()

    await page.getByTestId('cp-nav-discover').click()
    await expect(page.getByTestId('cp-discover-page')).toBeVisible()
    await page.getByTestId('cp-discover-search-input').fill('Digital Marketing')
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

    await page.waitForURL(/\/portal/)
    await expect(page.getByTestId('cp-portal-entry-banner')).toBeVisible()
    await expect(page.getByText('Setup is still required for Digital Marketing Agent')).toBeVisible()
    await expect(page.getByText('My Agents')).toBeVisible()
    await page.getByTestId('cp-portal-entry-primary').click()
    await page.getByRole('button', { name: /Review and activate/i }).click()
    await page.getByRole('button', { name: 'Open YouTube setup' }).click()
    await expect(page.getByText(/platform connections/i)).toBeVisible()
    await expect(page.getByText('YouTube channel status')).toBeVisible()
  })
})
