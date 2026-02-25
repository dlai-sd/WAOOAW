/**
 * E2E: Hire Wizard Journey
 *
 * Tests the full hire wizard flow:
 *   Draft creation → step advance → coupon apply → payment confirm → trial active
 *
 * Set SKIP_E2E=true or omit BASE_URL to skip when the full stack isn't up.
 */

import { test, expect } from '@playwright/test';

const SKIP = !process.env.BASE_URL || process.env.SKIP_E2E === 'true';

test.describe('Hire Wizard Journey', () => {

  test.beforeEach(async ({ page }) => {
    if (SKIP) return;
    // Pre-authenticate via localStorage token injection for E2E
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('access_token', 'e2e-test-token');
      localStorage.setItem('user_id', 'e2e-test-user');
    });
  });

  test('customer can complete the hire wizard end-to-end', async ({ page }) => {
    if (SKIP) {
      test.skip(true, 'Skipping E2E: BASE_URL not set or SKIP_E2E=true');
    }

    // Navigate to an agent profile
    await page.goto('/agents/agent-001');
    await expect(page.getByRole('heading')).toBeVisible();

    // Start hire wizard
    await page.getByRole('button', { name: /hire agent|start trial/i }).click();
    await expect(page.getByText(/step 1|wizard/i)).toBeVisible({ timeout: 10000 });

    // Step 1 — confirm agent selection
    await page.getByRole('button', { name: /continue|next/i }).click();
    await expect(page.getByText(/step 2|payment|coupon/i)).toBeVisible({ timeout: 10000 });

    // Apply coupon
    const couponInput = page.locator('input[name="coupon"], input[placeholder*="coupon" i]');
    if (await couponInput.isVisible()) {
      await couponInput.fill('TRIAL10');
      await page.getByRole('button', { name: /apply/i }).click();
      await expect(page.getByText(/discount|10%/i)).toBeVisible({ timeout: 5000 });
    }

    // Confirm payment
    await page.getByRole('button', { name: /confirm|pay|complete/i }).click();

    // Assert hire confirmed and trial started
    await expect(page.getByText(/hired|confirmed|trial.*started|success/i)).toBeVisible({
      timeout: 15000,
    });
  });

  test('customer can cancel the hire wizard', async ({ page }) => {
    if (SKIP) {
      test.skip(true, 'Skipping E2E: BASE_URL not set or SKIP_E2E=true');
    }

    await page.goto('/agents/agent-001');
    await page.getByRole('button', { name: /hire agent|start trial/i }).click();
    await expect(page.getByText(/step 1|wizard/i)).toBeVisible({ timeout: 10000 });

    await page.getByRole('button', { name: /cancel/i }).click();

    // Should return to agent page or discover page
    await expect(page).toHaveURL(/agents|discover/i, { timeout: 10000 });
  });
});
