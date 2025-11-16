import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,  // Run sequentially for flow tests
  timeout: 30000,
  expect: { timeout: 5000 },

  use: {
    baseURL: 'http://localhost:3001',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    viewport: { width: 1280, height: 720 },
    // Disable animations for consistent screenshots
    actionTimeout: 10000,
  },

  projects: [
    {
      name: 'chromium',
      use: {
        browserName: 'chromium',
      }
    }
  ],

  // Start dev server before tests
  webServer: {
    command: 'cd frontend && npm run dev',
    port: 3001,
    reuseExistingServer: true,
    timeout: 120000,
  },

  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list']
  ],
});
