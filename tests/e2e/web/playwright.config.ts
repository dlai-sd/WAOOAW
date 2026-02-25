import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: '.',
  timeout: 30000,
  use: {
    baseURL: process.env.BASE_URL || 'http://plant-gateway-test:8000',
    headless: true,
  },
  reporter: [['html', { outputFolder: 'reports' }]],
});
