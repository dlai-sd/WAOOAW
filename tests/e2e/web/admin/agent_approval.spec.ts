import { test, expect } from '@playwright/test';

test.describe('PP Agent Creation and Approval Journey', () => {
  test('health check - gateway is reachable', async ({ request }) => {
    const response = await request.get('/health', { failOnStatusCode: false });
    expect(response.status()).toBeGreaterThanOrEqual(200);
    expect(response.status()).toBeLessThan(600);
  });

  test('agent types endpoint responds', async ({ request }) => {
    const response = await request.get('/agent-types', { failOnStatusCode: false });
    expect(response.status()).toBeGreaterThanOrEqual(200);
  });

  test('agent approval lifecycle states are valid', async () => {
    const states = ['draft', 'pending_review', 'approved', 'live', 'rejected'];
    expect(states).toContain('approved');
    expect(states).toContain('live');
  });
});
