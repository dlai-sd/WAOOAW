import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: '.',
  outputDir: 'reports',
  reporter: [['html', { outputFolder: 'reports', open: 'never' }]],
  use: {
    baseURL: process.env.BASE_URL || 'http://plant-gateway-test:8000',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
