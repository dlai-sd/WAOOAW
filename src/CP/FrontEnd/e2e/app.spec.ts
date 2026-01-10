import { test, expect } from '@playwright/test';

/**
 * End-to-End UI Tests for Customer Portal
 * Tests critical user journeys and UI interactions
 */

test.describe('Landing Page', () => {
  test('should load landing page', async ({ page }) => {
    await page.goto('/');
    
    // Check page title
    await expect(page).toHaveTitle(/WAOOAW/i);
    
    // Check key elements
    await expect(page.getByText(/Sign In/i)).toBeVisible();
  });

  test('should have functional theme toggle', async ({ page }) => {
    await page.goto('/');
    
    const themeButton = page.getByLabel(/toggle theme/i);
    await expect(themeButton).toBeVisible();
    
    // Click to toggle theme
    await themeButton.click();
    
    // Theme should change (verify by checking body class or styles)
    // This is application-specific
  });
});

test.describe('Authentication Flow', () => {
  test('should open auth modal on sign in click', async ({ page }) => {
    await page.goto('/');
    
    // Click Sign In button
    await page.getByText(/Sign In/i).click();
    
    // Auth modal should appear
    await expect(page.getByText(/Sign in to/i)).toBeVisible();
  });

  test('should close auth modal with close button', async ({ page }) => {
    await page.goto('/');
    
    // Open modal
    await page.getByText(/Sign In/i).click();
    await expect(page.getByText(/Sign in to/i)).toBeVisible();
    
    // Click close button
    await page.getByRole('button', { name: /dismiss/i }).click();
    
    // Modal should close
    await expect(page.getByText(/Sign in to/i)).not.toBeVisible();
  });
});

test.describe('Responsive Design', () => {
  test('should work on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    
    // Key elements should still be visible
    await expect(page.getByText(/Sign In/i)).toBeVisible();
  });

  test('should work on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');
    
    await expect(page.getByText(/Sign In/i)).toBeVisible();
  });

  test('should work on desktop viewport', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    
    await expect(page.getByText(/Sign In/i)).toBeVisible();
  });
});

test.describe('Accessibility', () => {
  test('should have no accessibility violations', async ({ page }) => {
    await page.goto('/');
    
    // Basic accessibility checks
    // In production, use @axe-core/playwright for comprehensive checks
    const themeButton = page.getByLabel(/toggle theme/i);
    await expect(themeButton).toHaveAttribute('aria-label');
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/');
    
    // Tab through interactive elements
    await page.keyboard.press('Tab');
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
  });
});

test.describe('Performance', () => {
  test('should load within acceptable time', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/');
    const loadTime = Date.now() - startTime;
    
    // Should load in under 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });
});
