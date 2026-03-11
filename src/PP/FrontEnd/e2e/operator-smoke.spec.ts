import { expect, test } from '@playwright/test'

function createJwt(userId: string): string {
  const header = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64url')
  const payload = Buffer.from(
    JSON.stringify({
      user_id: userId,
      email: 'operator@waooaw.com',
      token_type: 'access',
      exp: Math.floor(Date.now() / 1000) + 60 * 60,
      iat: Math.floor(Date.now() / 1000),
      roles: ['admin'],
    })
  ).toString('base64url')

  return `${header}.${payload}.pp-operator-signature`
}

test.describe('PP operator smoke', () => {
  test('moves from review queue to DMA runtime diagnostics and back to review queue handoff', async ({ page }) => {
    const accessToken = createJwt('pp-operator-user')

    await page.route('**/api/**', async (route) => {
      const request = route.request()
      const url = new URL(request.url())
      const path = url.pathname
      const method = request.method()

      if (path.endsWith('/api/auth/dev-token') && method === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ access_token: accessToken }),
        })
        return
      }

      if (path.endsWith('/api/pp/approvals/review-queue')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            count: 1,
            approvals: [
              {
                approval_id: 'APR-PP-1',
                customer_id: 'CUST-PP-1',
                customer_label: 'Care Clinic',
                agent_id: 'AGT-MKT-DMA-001',
                agent_label: 'Digital Marketing Agent',
                action: 'publish',
                requested_by: 'ops-admin',
                correlation_id: 'corr-pp-1',
                purpose: 'review_queue',
                notes: 'Check the runtime before approving.',
                created_at: '2026-03-10T13:00:00Z',
                expires_at: null,
                hired_instance_id: 'HIRE-PP-1',
                review_state: 'pending_review',
                deliverable_preview: {
                  batch_id: 'BATCH-1',
                  post_id: 'POST-1',
                  brand_name: 'Care Clinic',
                  theme: 'Healthy habits for busy parents',
                  channel: 'youtube',
                  text_preview: 'Preview script for the next YouTube explainer',
                },
                publish_diagnostics: {
                  publish_block: 'credential_missing',
                  publish_reason: 'The draft is approved, but the YouTube credential reference is still missing.',
                  credential_state: 'missing_youtube_credential_ref',
                  approval_lineage: 'Approval APR-PP-1 is currently attached to post POST-1.',
                  youtube_visibility: 'private',
                  public_release_requested: false,
                  last_error: 'credential_ref_required_for_youtube_publish',
                },
              },
            ],
          }),
        })
        return
      }

      if (path.endsWith('/api/pp/ops/subscriptions')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              subscription_id: 'SUB-PP-1',
              agent_id: 'AGT-MKT-DMA-001',
              status: 'active',
              duration: 'monthly',
            },
          ]),
        })
        return
      }

      if (path.endsWith('/api/pp/ops/hired-agents')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              hired_instance_id: 'HIRE-PP-1',
              subscription_id: 'SUB-PP-1',
              agent_id: 'AGT-MKT-DMA-001',
              configured: true,
              goals_completed: true,
              trial_status: 'active',
              config: { timezone: 'Asia/Kolkata' },
            },
          ]),
        })
        return
      }

      if (path.endsWith('/api/pp/ops/hired-agents/HIRE-PP-1/goals')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            hired_instance_id: 'HIRE-PP-1',
            goals: [
              {
                goal_instance_id: 'GOI-1',
                goal_template_id: 'marketing.daily_youtube_short.v1',
                frequency: 'three_per_week',
                settings: { platform: 'youtube' },
              },
            ],
          }),
        })
        return
      }

      if (path.endsWith('/api/pp/ops/hired-agents/HIRE-PP-1/deliverables')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            hired_instance_id: 'HIRE-PP-1',
            deliverables: [
              {
                deliverable_id: 'DEL-1',
                goal_template_id: 'marketing.daily_youtube_short.v1',
                frequency: 'three_per_week',
                review_status: 'approved',
                approval_id: 'APR-PP-1',
                execution_status: 'not_executed',
                payload: {
                  destination: {
                    destination_type: 'youtube',
                    metadata: { visibility: 'private' },
                    publish_status: 'not_published',
                  },
                },
                created_at: '2026-03-10T13:05:00Z',
              },
            ],
          }),
        })
        return
      }

      if (path.endsWith('/api/pp/ops/hired-agents/HIRE-PP-1/skills')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              skill_id: 'skill-theme-discovery',
              display_name: 'Theme Discovery',
              goal_schema: { fields: [{ key: 'business_name', label: 'Business name', required: true }] },
              goal_config: { business_name: 'WAOOAW Studio' },
            },
          ]),
        })
        return
      }

      if (path.endsWith('/api/pp/ops/hired-agents/HIRE-PP-1/platform-connections')) {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
        return
      }

      if (path.endsWith('/api/pp/approvals')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            count: 1,
            approvals: [
              {
                approval_id: 'APR-PP-1',
                customer_id: 'CUST-PP-1',
                agent_id: 'AGT-MKT-DMA-001',
                action: 'publish',
                correlation_id: 'corr-pp-1',
                created_at: '2026-03-10T13:00:00Z',
                expires_at: null,
              },
            ],
          }),
        })
        return
      }

      if (path.endsWith('/api/v1/audit/policy-denials')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            count: 1,
            records: [
              {
                created_at: '2026-03-10T13:02:00Z',
                correlation_id: 'corr-pp-1',
                decision_id: 'DEC-1',
                agent_id: 'AGT-MKT-DMA-001',
                customer_id: 'CUST-PP-1',
                action: 'publish',
                reason: 'approval_required_for_youtube_publish',
                path: '/api/v1/deliverables/DEL-1/execute',
                details: { message: 'missing approval_id' },
              },
            ],
          }),
        })
        return
      }

      if (path.endsWith('/api/v1/customers/lookup')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ customer_id: 'CUST-PP-1', email: 'care@clinic.com' }),
        })
        return
      }

      if (path.endsWith('/api/pp/ops/hired-agents/HIRE-PP-1/construct-health')) {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) })
        return
      }

      if (path.endsWith('/api/pp/ops/hired-agents/HIRE-PP-1/scheduler-diagnostics')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            hired_agent_id: 'HIRE-PP-1',
            cron_expression: '0 9 * * 1-5',
            next_run_at: '2026-03-12T09:00:00Z',
            last_run_at: '2026-03-11T09:00:00Z',
            lag_seconds: 60,
            dlq_depth: 1,
            dlq_entries: [
              {
                dlq_id: 'dlq-1',
                hired_agent_id: 'HIRE-PP-1',
                failed_at: '2026-03-11T09:01:00Z',
                hook_stage: 'pre_publish',
                error_message: 'credential_ref_required_for_youtube_publish',
                retry_count: 1,
              },
            ],
            tasks_used_today: 2,
            trial_task_limit: 10,
            pause_state: 'RUNNING',
            latest_failure_reason: 'credential_ref_required_for_youtube_publish',
            latest_approval_id: 'APR-PP-1',
            latest_deliverable_id: 'DEL-1',
          }),
        })
        return
      }

      if (path.endsWith('/api/pp/ops/hired-agents/HIRE-PP-1/hook-trace')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              event_id: 'evt-1',
              stage: 'pre_publish',
              hired_agent_id: 'HIRE-PP-1',
              agent_type: 'marketing',
              result: 'halt',
              reason: 'approval_required_for_youtube_publish',
              emitted_at: '2026-03-11T09:01:00Z',
              payload_summary: 'approval_id=APR-PP-1 deliverable_id=DEL-1',
              hook_class: 'ApprovalGateHook',
            },
          ]),
        })
        return
      }

      if (path.endsWith('/api/v1/marketing/draft-posts/POST-1/approve') && method === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ post_id: 'POST-1', review_status: 'approved', approval_id: 'APR-PP-1' }),
        })
        return
      }

      if (path.endsWith('/api/v1/marketing/draft-posts/POST-1/reject') && method === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ post_id: 'POST-1', review_status: 'rejected' }),
        })
        return
      }

      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) })
    })

    await page.goto('/')
    await expect(page.getByTestId('pp-public-shell')).toBeVisible()

    await page.getByTestId('pp-signin-trigger').click()
    await page.getByTestId('pp-demo-login-button').click()

    await expect(page.getByTestId('pp-dashboard-page')).toBeVisible()
    await page.getByTestId('pp-nav-draft-review').click()

    await expect(page.getByTestId('pp-review-queue-page')).toBeVisible()
    await page.getByTestId('pp-review-queue-customer-id').fill('CUST-PP-1')
    await page.getByTestId('pp-review-queue-agent-id').fill('AGT-MKT-DMA-001')
    await page.getByTestId('pp-review-queue-correlation-id').fill('corr-pp-1')
    await page.getByTestId('pp-review-queue-load').click()

    await expect(page.getByTestId('pp-review-queue-workspace')).toBeVisible()
    await expect(page.getByTestId('pp-review-queue-workspace').getByText('approval_id: APR-PP-1', { exact: true })).toBeVisible()
    await expect(page.getByTestId('pp-review-queue-workspace').getByText('Preview script for the next YouTube explainer')).toBeVisible()
    await expect(page.getByTestId('pp-review-queue-publish-readiness')).toContainText('Blocked by channel connection')
    await expect(page.getByTestId('pp-review-queue-channel-status')).toContainText('Youtube not connected')

    await page.getByTestId('pp-review-queue-open-runtime-context').click()

    await expect(page.getByTestId('pp-hired-agents-page')).toBeVisible()
    await expect(page.getByTestId('pp-hired-agents-row-HIRE-PP-1')).toBeVisible()
    await expect(page.getByTestId('pp-dma-brief-summary-card')).toBeVisible()
    await expect(page.getByText('WAOOAW Studio')).toBeVisible()
    await expect(page.getByTestId('pp-dma-publish-readiness')).toContainText('Blocked by channel connection')
    await expect(page.getByTestId('pp-dma-channel-status')).toContainText('Youtube not connected')

    await page.locator('button').filter({ hasText: 'Scheduler' }).click()
    await expect(page.getByTestId('pp-scheduler-blocker-label')).toContainText('Missing YouTube credential')

    await page.locator('button').filter({ hasText: 'Hook Trace' }).click()
    await expect(page.getByTestId('pp-hook-trace-signal-label')).toContainText('Approval gate halted publish')

    await page.getByTestId('pp-hired-agents-open-review-queue').click()

    await expect(page.getByTestId('pp-review-queue-page')).toBeVisible()
    await expect(page.getByTestId('pp-review-queue-customer-id')).toHaveValue('CUST-PP-1')
    await expect(page.getByTestId('pp-review-queue-agent-id')).toHaveValue('AGT-MKT-DMA-001')
    await expect(page.getByTestId('pp-review-queue-correlation-id')).toHaveValue('corr-pp-1')
  })
})