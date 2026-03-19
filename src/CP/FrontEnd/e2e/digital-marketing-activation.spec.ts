import { expect, test } from '@playwright/test'

test.describe('Digital Marketing activation wizard', () => {
  test('covers the full wizard path through runtime-ready confirmation with mocked APIs', async ({ page }) => {
    const workspace = {
      hired_instance_id: 'HAI-DMA-1',
      help_visible: false,
      activation_complete: false,
      induction: {
        nickname: 'Growth Copilot',
        theme: 'dark',
        primary_language: 'en',
        timezone: 'Asia/Kolkata',
        brand_name: 'WAOOAW',
        offerings_services: ['Activation'],
        location: 'Pune',
        target_audience: 'Founders',
        notes: '',
      },
      prepare_agent: {
        selected_platforms: ['youtube', 'instagram'],
        platform_steps: [
          { platform_key: 'youtube', complete: false, status: 'pending' },
          { platform_key: 'instagram', complete: false, status: 'pending' },
        ],
        all_selected_platforms_completed: false,
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
      updated_at: '2026-03-18T09:00:00Z',
    }

    await page.route('**/api/**', async (route) => {
      const { pathname } = new URL(route.request().url())
      const method = route.request().method()

      if (pathname.endsWith('/api/auth/refresh')) {
        await route.fulfill({ status: 401, body: JSON.stringify({ detail: 'No refresh session' }) })
        return
      }

      if (pathname.endsWith('/api/auth/me')) {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ id: 'cp-user', email: 'customer@waooaw.com' }) })
        return
      }

      if (pathname.endsWith('/api/cp/my-agents/summary')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            instances: [
              {
                subscription_id: 'SUB-DMA-1',
                agent_id: 'AGT-MKT-DMA-001',
                agent_type_id: 'marketing.digital_marketing.v1',
                duration: 'monthly',
                status: 'active',
                current_period_start: '2026-03-01T00:00:00Z',
                current_period_end: '2026-04-01T00:00:00Z',
                cancel_at_period_end: false,
                hired_instance_id: 'HAI-DMA-1',
                nickname: 'Growth Copilot',
              },
            ],
          }),
        })
        return
      }

      if (pathname.endsWith('/api/cp/digital-marketing-activation/HAI-DMA-1') && method === 'GET') {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(workspace) })
        return
      }

      if (pathname.endsWith('/api/cp/digital-marketing-activation/HAI-DMA-1') && method === 'PATCH') {
        const patch = route.request().postDataJSON() as Record<string, any>
        Object.assign(workspace, patch)
        workspace.induction = { ...workspace.induction, ...(patch.induction || {}) }
        workspace.prepare_agent = { ...workspace.prepare_agent, ...(patch.prepare_agent || {}) }
        workspace.campaign_setup = { ...workspace.campaign_setup, ...(patch.campaign_setup || {}) }
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(workspace) })
        return
      }

      if (pathname.endsWith('/generate-theme-plan')) {
        workspace.campaign_setup.master_theme = 'Trust-first growth'
        workspace.campaign_setup.derived_themes = [
          { title: 'Proof', description: 'Show results', frequency: 'weekly' },
          { title: 'Education', description: 'Teach the market', frequency: 'weekly' },
        ]
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            campaign_id: 'CAM-DMA-1',
            master_theme: workspace.campaign_setup.master_theme,
            derived_themes: workspace.campaign_setup.derived_themes,
            workspace,
          }),
        })
        return
      }

      if (pathname.endsWith('/theme-plan')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            campaign_id: 'CAM-DMA-1',
            master_theme: workspace.campaign_setup.master_theme,
            derived_themes: workspace.campaign_setup.derived_themes,
            workspace,
          }),
        })
        return
      }

      if (pathname.endsWith('/api/cp/hired-agents/HAI-DMA-1/platform-connections')) {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
        return
      }

      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) })
    })

    await page.goto('/')
    await page.getByText('My Agents').click()
    await expect(page.getByText('Induct Agent')).toBeVisible()
    await page.getByRole('button', { name: 'Show Help' }).click()
    await expect(page.getByTestId('dma-help-panel-primary')).toBeVisible()
    await page.getByText('Prepare Agent').click()
    await page.getByRole('button', { name: 'Mark prepared' }).first().click()
    await page.getByText('Master Theme').click()
    await page.getByRole('button', { name: 'Generate theme plan' }).click()
    await expect(page.getByDisplayValue('Trust-first growth')).toBeVisible()
  })
})
