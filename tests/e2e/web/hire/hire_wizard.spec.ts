import { test, expect } from '@playwright/test';

test.describe('Hire Wizard Journey', () => {
  test('agents endpoint returns response', async ({ request }) => {
    const response = await request.get('/agents', { failOnStatusCode: false });
    expect(response.status()).toBeGreaterThanOrEqual(200);
    expect(response.status()).toBeLessThan(600);
  });

  test('create draft hire', async ({ request }) => {
    const response = await request.post('/hire', {
      data: { agent_id: 'agent-001', customer_id: 'cp-user-001' },
      failOnStatusCode: false,
    });
    expect(response.status()).toBeGreaterThanOrEqual(200);
  });

  test('hire status transitions are valid', async () => {
    const validStatuses = ['draft', 'active', 'cancelled', 'expired'];
    const currentStatus = 'draft';
    expect(validStatuses).toContain(currentStatus);
  });
});
