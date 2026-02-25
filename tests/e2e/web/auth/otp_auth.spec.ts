/**
 * E2E: OTP Authentication Journey
 *
 * Tests the full OTP login flow:
 *   Navigate → Enter phone → Send OTP → Enter OTP → Verify → Dashboard
 *
 * Set SKIP_E2E=true or omit BASE_URL to skip when the full stack isn't up.
 */

import { test, expect } from '@playwright/test';

const SKIP = !process.env.BASE_URL || process.env.SKIP_E2E === 'true';

test.describe('OTP Authentication Journey', () => {

  test('user can log in via OTP and reach the dashboard', async ({ page }) => {
    if (SKIP) {
      test.skip(true, 'Skipping E2E: BASE_URL not set or SKIP_E2E=true');
    }

    // Navigate to CP login page
    await page.goto('/login');
    await expect(page).toHaveTitle(/WAOOAW|Login/i);

    // Enter phone number
    const phoneInput = page.getByPlaceholder(/phone/i).or(page.locator('input[type="tel"]'));
    await phoneInput.fill('+919876543210');

    // Request OTP
    await page.getByRole('button', { name: /send otp/i }).click();
    await expect(page.getByText(/enter.*otp|otp sent/i)).toBeVisible({ timeout: 10000 });

    // Enter OTP (test environment uses static OTP 123456)
    const otpInput = page.getByPlaceholder(/otp|code/i).or(page.locator('input[name="otp"]'));
    await otpInput.fill('123456');

    // Verify
    await page.getByRole('button', { name: /verify|submit/i }).click();

    // Confirm dashboard is loaded
    await expect(page).toHaveURL(/dashboard|home/i, { timeout: 15000 });
    await expect(page.getByText(/dashboard|home|agents/i)).toBeVisible();
  });

  test('invalid OTP shows an error message', async ({ page }) => {
    if (SKIP) {
      test.skip(true, 'Skipping E2E: BASE_URL not set or SKIP_E2E=true');
    }

    await page.goto('/login');

    const phoneInput = page.getByPlaceholder(/phone/i).or(page.locator('input[type="tel"]'));
    await phoneInput.fill('+919876543210');
    await page.getByRole('button', { name: /send otp/i }).click();

    const otpInput = page.getByPlaceholder(/otp|code/i).or(page.locator('input[name="otp"]'));
    await otpInput.fill('000000'); // wrong OTP

    await page.getByRole('button', { name: /verify|submit/i }).click();

    await expect(page.getByText(/invalid|incorrect|error/i)).toBeVisible({ timeout: 10000 });
  });
});
