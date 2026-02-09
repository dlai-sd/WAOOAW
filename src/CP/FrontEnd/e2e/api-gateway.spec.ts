/**
 * E2E Tests for API Gateway Implementation
 * End-to-end testing with Playwright (MVP-001, MVP-002, MVP-003)
 */

import { test, expect } from '@playwright/test'

test.skip(
  !process.env.E2E_FULLSTACK,
  'Requires full-stack backend services (auth + data APIs) beyond Vite preview'
)

test.describe('API Gateway E2E Tests', () => {
  test.describe('Trial Flow (MVP-001)', () => {
    test('should create a trial end-to-end', async ({ page }) => {
      // Navigate to CP portal
      await page.goto('/')

      // Login (assuming OAuth is mocked or test user exists)
      // In real test, this would go through auth flow

      // Navigate to agent discovery
      await page.goto('/discover')
      await expect(page).toHaveURL(/.*discover/)

      // Click on an agent to start trial
      const agentCard = page.locator('[data-testid="agent-card"]').first()
      await agentCard.click()

      // Should navigate to agent detail
      await expect(page).toHaveURL(/.*agent\/.*/)

      // Click "Start Trial" button
      const startTrialButton = page.locator(
        'button:has-text("Start 7-Day Trial")'
      )
      await startTrialButton.click()

      // Fill trial form
      await page.fill('[name="customer_email"]', 'e2e.test@example.com')
      await page.fill('[name="customer_name"]', 'E2E Test User')
      await page.fill('[name="customer_company"]', 'Test Company')
      await page.fill('[name="customer_phone"]', '+1234567890')

      // Submit trial
      await page.click('button[type="submit"]')

      // Verify success message or redirect
      await expect(page.locator('text=Trial started')).toBeVisible({
        timeout: 5000,
      })
    })

    test('should list trials in dashboard', async ({ page }) => {
      await page.goto('/trials')

      // Wait for trials to load
      await expect(page.locator('[data-testid="trial-list"]')).toBeVisible(
        {
          timeout: 5000,
        }
      )

      // Verify table headers
      await expect(page.locator('th:has-text("Agent")')).toBeVisible()
      await expect(page.locator('th:has-text("Status")')).toBeVisible()
      await expect(
        page.locator('th:has-text("Days Remaining")')
      ).toBeVisible()
    })

    test('should filter trials by status', async ({ page }) => {
      await page.goto('/trials')

      // Select filter
      await page.selectOption('[name="status_filter"]', 'active')

      // Wait for filtered results
      await page.waitForTimeout(500)

      // All visible trials should have "Active" status
      const statusBadges = page.locator('[data-testid="trial-status"]')
      const count = await statusBadges.count()

      for (let i = 0; i < count; i++) {
        const text = await statusBadges.nth(i).textContent()
        expect(text?.toLowerCase()).toContain('active')
      }
    })
  })

  test.describe('Authentication Flow (MVP-002)', () => {
    test('should register new user with email/password', async ({
      page,
    }) => {
      await page.goto('/')

      // Click register button
      await page.click('button:has-text("Sign Up")')

      // Fill registration form
      const uniqueEmail = `e2e.${Date.now()}@example.com`
      await page.fill('[name="email"]', uniqueEmail)
      await page.fill('[name="password"]', 'TestPass123!')
      await page.fill('[name="full_name"]', 'E2E Test User')

      // Submit
      await page.click('button[type="submit"]')

      // Should redirect to portal or show success
      await expect(
        page.locator('text=Welcome') ||
          page.locator('[data-testid="authenticated-portal"]')
      ).toBeVisible({ timeout: 5000 })
    })

    test('should login existing user', async ({ page }) => {
      await page.goto('/')

      // Click login button
      await page.click('button:has-text("Log In")')

      // Fill login form
      await page.fill('[name="email"]', 'test@example.com')
      await page.fill('[name="password"]', 'TestPass123!')

      // Submit
      await page.click('button[type="submit"]')

      // Should be authenticated
      await expect(page).toHaveURL(/.*portal/)
      await expect(
        page.locator('[data-testid="user-profile"]')
      ).toBeVisible()
    })

    test('should show error for invalid credentials', async ({ page }) => {
      await page.goto('/')

      await page.click('button:has-text("Log In")')
      await page.fill('[name="email"]', 'test@example.com')
      await page.fill('[name="password"]', 'WrongPassword!')
      await page.click('button[type="submit"]')

      // Should show error message
      await expect(
        page.locator('text=Invalid credentials') ||
          page.locator('[role="alert"]')
      ).toBeVisible()
    })

    test('should logout user', async ({ page, context }) => {
      // Login first
      await page.goto('/')
      await page.click('button:has-text("Log In")')
      await page.fill('[name="email"]', 'test@example.com')
      await page.fill('[name="password"]', 'TestPass123!')
      await page.click('button[type="submit"]')

      await expect(page).toHaveURL(/.*portal/)

      // Logout
      await page.click('[data-testid="logout-button"]')

      // Should redirect to landing page
      await expect(page).toHaveURL(/\/$/)

      // Verify localStorage is cleared
      const token = await page.evaluate(
        () => localStorage.getItem('access_token')
      )
      expect(token).toBeNull()
    })
  })

  test.describe('Navigation Flow (MVP-003)', () => {
    test('should navigate without page reload', async ({ page }) => {
      await page.goto('/portal')

      // Click navigation link
      await page.click('a[href="/discover"]')

      // Should navigate client-side (no page reload)
      await expect(page).toHaveURL(/.*discover/)

      // Page should not have reloaded (SPA behavior)
      const navigation = page.waitForNavigation({ timeout: 100 })
      await expect(navigation).rejects.toThrow()
    })

    test('should use browser back/forward buttons', async ({ page }) => {
      await page.goto('/portal')
      await page.goto('/discover')
      await page.goto('/trials')

      // Go back
      await page.goBack()
      await expect(page).toHaveURL(/.*discover/)

      // Go back again
      await page.goBack()
      await expect(page).toHaveURL(/.*portal/)

      // Go forward
      await page.goForward()
      await expect(page).toHaveURL(/.*discover/)
    })

    test('should handle protected route redirect', async ({ page }) => {
      // Visit protected route while logged out
      await page.goto('/trials')

      // Should redirect to landing page
      await expect(page).toHaveURL(/\/$/)
      await expect(page.locator('text=Sign In')).toBeVisible()
    })

    test('should preserve state during navigation', async ({ page }) => {
      await page.goto('/portal')

      // Set some UI state (e.g., theme preference)
      await page.evaluate(() => {
        localStorage.setItem('theme', 'dark')
      })

      // Navigate to another page
      await page.goto('/discover')

      // State should be preserved
      const theme = await page.evaluate(
        () => localStorage.getItem('theme')
      )
      expect(theme).toBe('dark')
    })
  })

  test.describe('Integration Tests', () => {
    test('should complete full trial workflow', async ({ page }) => {
      // 1. Register
      await page.goto('/')
      await page.click('button:has-text("Sign Up")')
      const email = `workflow.${Date.now()}@example.com`
      await page.fill('[name="email"]', email)
      await page.fill('[name="password"]', 'WorkflowPass123!')
      await page.fill('[name="full_name"]', 'Workflow User')
      await page.click('button[type="submit"]')

      // 2. Navigate to agent discovery
      await page.goto('/discover')

      // 3. Select an agent
      await page.click('[data-testid="agent-card"]')

      // 4. Start trial
      await page.click('button:has-text("Start Trial")')
      await page.fill('[name="customer_email"]', email)
      await page.fill('[name="customer_name"]', 'Workflow User')
      await page.click('button[type="submit"]')

      // 5. View trials dashboard
      await page.goto('/trials')
      await expect(
        page.locator(`text=${email}`) ||
          page.locator('[data-testid="trial-email"]')
      ).toBeVisible()

      // 6. Logout
      await page.click('[data-testid="logout-button"]')
      await expect(page).toHaveURL(/\/$/)
    })
  })

  test.describe('Performance Tests', () => {
    test('should load agent discovery within 2 seconds', async ({
      page,
    }) => {
      const startTime = Date.now()

      await page.goto('/discover')
      await expect(
        page.locator('[data-testid="agent-list"]')
      ).toBeVisible()

      const loadTime = Date.now() - startTime
      expect(loadTime).toBeLessThan(2000)
    })

    test('should handle rapid navigation', async ({ page }) => {
      await page.goto('/portal')

      // Rapid navigation
      for (let i = 0; i < 5; i++) {
        await page.click('a[href="/discover"]')
        await page.click('a[href="/trials"]')
        await page.click('a[href="/portal"]')
      }

      // Should still be functional
      await expect(page).toHaveURL(/.*portal/)
      await expect(page.locator('body')).toBeVisible()
    })
  })
})
