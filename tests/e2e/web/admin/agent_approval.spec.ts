/**
 * E2E: PP Agent Creation and Approval Journey
 *
 * Tests the agent approval flow from the Partner Portal (PP):
 *   Create agent → submit for approval → approve → agent goes live
 *
 * Set SKIP_E2E=true or omit BASE_URL to skip when the full stack isn't up.
 */

import { test, expect } from '@playwright/test';

const SKIP = !process.env.BASE_URL || process.env.SKIP_E2E === 'true';
const PP_BASE_URL = process.env.PP_BASE_URL || process.env.BASE_URL || 'http://pp-backend-test:8002';

test.describe('PP Agent Approval Journey', () => {

  test.beforeEach(async ({ page }) => {
    if (SKIP) return;
    // Inject admin token for PP portal
    await page.goto(PP_BASE_URL);
    await page.evaluate(() => {
      localStorage.setItem('access_token', 'e2e-admin-token');
      localStorage.setItem('role', 'admin');
    });
  });

  test('agent partner can create and submit an agent for approval', async ({ page }) => {
    if (SKIP) {
      test.skip(true, 'Skipping E2E: BASE_URL not set or SKIP_E2E=true');
    }

    // Navigate to agent creation
    await page.goto(`${PP_BASE_URL}/agents/new`);
    await expect(page.getByRole('heading', { name: /create agent|new agent/i })).toBeVisible();

    // Fill agent details
    await page.getByLabel(/name/i).fill('E2E Test Agent');
    await page.getByLabel(/specialty|specialization/i).fill('content-marketing');
    await page.getByLabel(/description/i).fill('An E2E test agent for approval flow.');

    // Submit form
    await page.getByRole('button', { name: /save|create/i }).click();
    await expect(page.getByText(/created|draft/i)).toBeVisible({ timeout: 10000 });

    // Submit for approval
    await page.getByRole('button', { name: /submit.*approval|request.*review/i }).click();
    await expect(page.getByText(/pending|submitted|under.*review/i)).toBeVisible({ timeout: 10000 });
  });

  test('admin can approve a pending agent and make it live', async ({ page }) => {
    if (SKIP) {
      test.skip(true, 'Skipping E2E: BASE_URL not set or SKIP_E2E=true');
    }

    // Navigate to admin approval queue
    await page.goto(`${PP_BASE_URL}/admin/agents/pending`);
    await expect(page.getByRole('heading', { name: /pending.*approval|review queue/i })).toBeVisible();

    // Approve the first pending agent
    const approveButton = page.getByRole('button', { name: /approve/i }).first();
    await expect(approveButton).toBeVisible({ timeout: 10000 });
    await approveButton.click();

    // Confirm agent is live
    await expect(page.getByText(/approved|live|active/i)).toBeVisible({ timeout: 10000 });
  });
});
