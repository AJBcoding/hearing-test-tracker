# Playwright E2E Testing Handoff

## Overview

This document outlines a comprehensive approach to end-to-end testing using Playwright, based on proven patterns from the Career Lexicon Builder project. This testing methodology emphasizes complete user journey validation with visual documentation through automated screenshots.

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Project Structure](#project-structure)
3. [Configuration Setup](#configuration-setup)
4. [Test Organization Patterns](#test-organization-patterns)
5. [Helper Functions](#helper-functions)
6. [Test Data Management](#test-data-management)
7. [Writing User Flow Tests](#writing-user-flow-tests)
8. [Screenshot Documentation](#screenshot-documentation)
9. [Best Practices](#best-practices)
10. [Running Tests](#running-tests)

---

## Testing Philosophy

### Core Principles

1. **Complete User Journeys**: Tests simulate entire user workflows from start to finish
2. **Sequential Execution**: Tests run in order to maintain state continuity across the journey
3. **Visual Documentation**: Screenshots capture every major step for documentation and debugging
4. **Phase-Based Organization**: Tests are grouped into logical phases (Authentication, Project Creation, Workspace Navigation, etc.)
5. **Resilient Patterns**: Tests handle edge cases (user already exists, already logged in, etc.)

### Why This Approach?

- **Real-world validation**: Tests mimic actual user behavior patterns
- **Comprehensive coverage**: Every step of the user journey is verified
- **Living documentation**: Screenshots serve as visual documentation of the application flow
- **Regression detection**: Visual changes are easily spotted through screenshot comparisons
- **Debugging efficiency**: Screenshots pinpoint exactly where failures occur

---

## Project Structure

```
your-project/
├── tests/
│   └── e2e/
│       ├── fixtures/
│       │   └── test-data.js          # Centralized test data
│       ├── helpers/
│       │   └── screenshot.js         # Screenshot utilities
│       └── user-flow.spec.js         # Main test suite
├── docs/
│   └── screenshots/
│       └── flow/                     # Auto-generated screenshots
│           ├── 01-login-page.png
│           ├── 01-login-page.json    # Screenshot metadata
│           ├── 02-registration-form.png
│           └── ...
└── playwright.config.js              # Playwright configuration
```

---

## Configuration Setup

### playwright.config.js

```javascript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,  // Run sequentially for flow tests
  timeout: 30000,
  expect: { timeout: 5000 },

  use: {
    baseURL: 'http://localhost:5174',
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
    command: 'npm run dev',
    port: 5174,
    reuseExistingServer: true,
    timeout: 120000,
  },

  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list']
  ],
});
```

### Key Configuration Points

- **`fullyParallel: false`**: Critical for sequential user journey tests
- **`viewport`**: Consistent viewport ensures reproducible screenshots
- **`webServer`**: Automatically starts your dev server before tests
- **`screenshot: 'only-on-failure'`**: Captures failures automatically (custom screenshots handled separately)

---

## Test Organization Patterns

### Phase-Based Test Structure

Tests are organized into logical phases that represent distinct parts of the user journey:

```javascript
test.describe('Complete User Journey', () => {

  // =================================================================
  // PHASE 1: AUTHENTICATION
  // =================================================================
  test.describe('Phase 1: Authentication', () => {
    test('01: Login page loads correctly', async ({ page }) => { /* ... */ });
    test('02: Registration form appears', async ({ page }) => { /* ... */ });
    test('03: Registration validation works', async ({ page }) => { /* ... */ });
    test('04: Successful registration and auto-login', async ({ page }) => { /* ... */ });
    test('05: Logout functionality works', async ({ page }) => { /* ... */ });
    test('06: Login with existing credentials', async ({ page }) => { /* ... */ });
  });

  // =================================================================
  // PHASE 2: PROJECT CREATION
  // =================================================================
  test.describe('Phase 2: Project Creation', () => {
    // beforeEach ensures logged-in state
    test.beforeEach(async ({ page }) => {
      // Login logic
    });

    test('07: Empty dashboard shows welcome message', async ({ page }) => { /* ... */ });
    test('08: Create project form appears', async ({ page }) => { /* ... */ });
    // ... more tests
  });

  // Additional phases...
});
```

### Test Numbering Convention

- **Sequential numbering**: Tests are numbered (01, 02, 03...) to indicate execution order
- **Descriptive names**: Each test name clearly describes what it validates
- **Phase alignment**: Numbers continue across phases to show complete journey

---

## Helper Functions

### screenshot.js - Screenshot Utilities

```javascript
import { writeFile } from 'fs/promises';
import path from 'path';

/**
 * Capture a screenshot of the current page state
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {number} stepNumber - Sequential step number (e.g., 1, 2, 3)
 * @param {string} description - Brief description (e.g., "login-page")
 * @returns {Promise<string>} - The filename of the captured screenshot
 */
export async function captureStep(page, stepNumber, description) {
  const timestamp = new Date().toISOString().split('T')[0];
  const paddedStep = stepNumber.toString().padStart(2, '0');
  const filename = `${paddedStep}-${description}.png`;

  const screenshotPath = path.join(
    process.cwd(),
    '..',
    'docs',
    'screenshots',
    'flow',
    filename
  );

  // Capture full page screenshot with animations disabled
  await page.screenshot({
    path: screenshotPath,
    fullPage: true,
    animations: 'disabled',
  });

  // Save metadata about the screenshot
  const metaPath = screenshotPath.replace('.png', '.json');
  const metadata = {
    description,
    timestamp,
    url: page.url(),
    viewport: page.viewportSize(),
    stepNumber,
  };

  await writeFile(metaPath, JSON.stringify(metadata, null, 2));

  console.log(`📸 Screenshot captured: ${filename}`);
  return filename;
}

/**
 * Capture a screenshot with hover state
 */
export async function captureHover(page, selector, stepNumber, description) {
  await page.hover(selector);
  await page.waitForTimeout(500);  // Ensure hover state is visible
  return await captureStep(page, stepNumber, description);
}

/**
 * Capture a screenshot after waiting for a specific element
 */
export async function captureAfterElement(page, selector, stepNumber, description) {
  await page.waitForSelector(selector, { state: 'visible' });
  return await captureStep(page, stepNumber, description);
}
```

### Benefits of Helper Functions

- **Consistent naming**: All screenshots follow the same naming pattern
- **Metadata tracking**: JSON files track when/where screenshots were taken
- **Debugging context**: Console logs confirm screenshot capture
- **Reusability**: Same helpers across all test files

---

## Test Data Management

### test-data.js - Centralized Test Data

```javascript
/**
 * Test data for E2E tests
 * These values are used across different test scenarios
 */

export const testUser = {
  fullName: 'Test User',
  email: 'test.user@example.com',
  password: 'testPassword123',
};

export const testProject = {
  institution: 'Test University',
  position: 'Associate Dean',
  deadline: '2026-03-01',
};

export const secondProject = {
  institution: 'Example College',
  position: 'Department Chair',
  deadline: '2026-04-15',
};

/**
 * Wait times for common scenarios (in milliseconds)
 */
export const waitTimes = {
  shortDelay: 500,
  navigation: 1000,
  apiResponse: 2000,
};

/**
 * Selectors for common elements
 */
export const selectors = {
  // Auth form
  fullNameInput: 'input[name="full_name"]',
  emailInput: 'input[name="email"]',
  passwordInput: 'input[name="password"]',
  loginButton: 'button[type="submit"]',
  registerTab: 'button:has-text("Register")',
  loginTab: 'button:has-text("Login")',
  logoutButton: 'button:has-text("Logout")',

  // Project dashboard
  newProjectButton: 'button:has-text("New Project")',
  institutionInput: 'input[value=""]',
  positionInput: 'input[type="text"]',
  deadlineInput: 'input[type="date"]',
  createProjectButton: 'button[type="submit"]:has-text("Create Project")',
  projectCard: '[key^="project"]',

  // Project workspace
  backToDashboardButton: 'button:has-text("Back to Dashboard")',
  fileUploadArea: 'input[type="file"], [data-testid="file-upload"]',

  // Common
  heading: 'h1, h2, h3',
  errorMessage: '[style*="error"], [class*="error"]',
};
```

### Benefits of Centralized Test Data

- **Single source of truth**: All tests reference the same data
- **Easy updates**: Change data in one place
- **Consistency**: Same user/project data across all tests
- **Readability**: Named constants make tests self-documenting

---

## Writing User Flow Tests

### Pattern 1: Basic Page Verification

```javascript
test('01: Login page loads correctly', async ({ page }) => {
  // Navigate to the application
  await page.goto('/');

  // Verify we're on the login page
  await expect(page.locator('h1')).toContainText('Your App Name');

  // Verify form elements are visible
  await expect(page.locator('button[type="submit"]:has-text("Login")')).toBeVisible();
  await expect(page.locator('input[name="email"]')).toBeVisible();
  await expect(page.locator('input[name="password"]')).toBeVisible();

  // Capture screenshot
  await captureStep(page, 1, 'login-page');
});
```

### Pattern 2: Form Interaction

```javascript
test('04: Successful registration', async ({ page }) => {
  await page.goto('/');
  await page.click('button:has-text("Register")');

  // Fill in form
  await page.fill('input[name="full_name"]', testUser.fullName);
  await page.fill('input[name="email"]', testUser.email);
  await page.fill('input[name="password"]', testUser.password);

  // Submit form
  await page.click('button[type="submit"]:has-text("Register")');

  // Wait for redirect
  await page.waitForTimeout(2000);

  // Verify success
  await expect(page.locator('button:has-text("Logout")')).toBeVisible({ timeout: 10000 });

  // Capture screenshot
  await captureStep(page, 4, 'dashboard-after-registration');
});
```

### Pattern 3: Resilient State Management

```javascript
test('06: Login with existing credentials', async ({ page }) => {
  await page.goto('/');

  // Check if already logged in
  const isLoggedIn = await page.locator('button:has-text("Logout")')
    .isVisible()
    .catch(() => false);

  if (!isLoggedIn) {
    // Need to login
    await page.fill('input[name="email"]', testUser.email);
    await page.fill('input[name="password"]', testUser.password);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/');
  }

  // Verify logged-in state
  await expect(page.locator('button:has-text("Logout")')).toBeVisible();

  // Capture screenshot
  await captureStep(page, 6, 'dashboard-after-login');
});
```

### Pattern 4: beforeEach for State Setup

```javascript
test.describe('Phase 2: Project Creation', () => {

  // Ensure user is logged in before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('/');

    // Check if already logged in
    const isLoggedIn = await page.locator('button:has-text("Logout")')
      .isVisible()
      .catch(() => false);

    if (!isLoggedIn) {
      await page.fill('input[name="email"]', testUser.email);
      await page.fill('input[name="password"]', testUser.password);
      await page.click('button[type="submit"]');
      await page.waitForURL('**/');
    }
  });

  test('07: Empty dashboard shows welcome message', async ({ page }) => {
    // Test starts with guaranteed logged-in state
    await expect(page.locator('button:has-text("Logout")')).toBeVisible();
    // ... rest of test
  });
});
```

### Pattern 5: Conditional Test Paths

```javascript
test('07: Empty dashboard shows welcome message', async ({ page }) => {
  // Check for welcome message
  const welcomeVisible = await page.locator('text=Welcome to Your App').isVisible();

  if (welcomeVisible) {
    // Empty state path
    await expect(page.locator('text=Get started by creating a project')).toBeVisible();
    await captureStep(page, 7, 'dashboard-empty-state');
  } else {
    // Projects exist path
    await expect(page.locator('button:has-text("New Project")')).toBeVisible();
    await captureStep(page, 7, 'dashboard-with-projects');
  }
});
```

---

## Screenshot Documentation

### Automatic Screenshot Generation

Every test captures screenshots at key moments, creating a visual record of the user journey.

### Screenshot Metadata

Each screenshot has an accompanying JSON file with metadata:

```json
{
  "description": "login-page",
  "timestamp": "2025-11-15",
  "url": "http://localhost:5174/",
  "viewport": {
    "width": 1280,
    "height": 720
  },
  "stepNumber": 1
}
```

### Using Screenshots

1. **Documentation**: Include in user guides or technical docs
2. **Debugging**: Compare current vs. expected UI
3. **Regression testing**: Visual diff to detect unintended changes
4. **Stakeholder demos**: Show complete user journey visually

---

## Best Practices

### 1. Test Independence vs. Flow

**For flow tests**: Sequential execution with state carryover is acceptable
```javascript
fullyParallel: false  // In config
```

**For unit/component tests**: Keep them independent and parallel

### 2. Selector Strategy

**Prefer semantic selectors**:
```javascript
// Good
await page.click('button:has-text("Login")');
await page.locator('input[name="email"]');

// Avoid (brittle)
await page.click('.btn-primary-123');
await page.locator('#input-0');
```

### 3. Wait Strategies

**Use Playwright's built-in waiting**:
```javascript
// Good - automatic waiting
await expect(page.locator('h1')).toBeVisible();
await page.click('button');

// Acceptable for specific cases
await page.waitForTimeout(500);  // For hover effects, animations

// Avoid hardcoded waits when possible
```

### 4. Error Handling

**Handle expected failures gracefully**:
```javascript
const isLoggedIn = await page.locator('button:has-text("Logout")')
  .isVisible()
  .catch(() => false);

if (!isLoggedIn) {
  // Handle login
}
```

### 5. Screenshot Timing

**Capture after actions complete**:
```javascript
await page.click('button[type="submit"]');
await page.waitForURL('**/dashboard');
await expect(page.locator('h1')).toBeVisible();
await captureStep(page, 8, 'dashboard-loaded');  // Capture when stable
```

### 6. Test Data Cleanup

**Consider data lifecycle**:
- Some tests may need database cleanup between runs
- Use unique test data (timestamps, random IDs) to avoid collisions
- Or implement teardown logic to clean up test artifacts

### 7. Documentation

**Document non-obvious patterns**:
```javascript
test('04: Registration with fallback to login', async ({ page }) => {
  // Note: User may already exist from previous test run
  // This test handles both registration and login scenarios

  await page.goto('/');
  // ... test implementation
});
```

---

## Running Tests

### Basic Commands

```bash
# Install dependencies
npm install @playwright/test

# Install browsers
npx playwright install

# Run all tests
npx playwright test

# Run specific test file
npx playwright test tests/e2e/user-flow.spec.js

# Run in UI mode (interactive)
npx playwright test --ui

# Run in headed mode (see browser)
npx playwright test --headed

# Generate test code (codegen)
npx playwright codegen http://localhost:5174
```

### Debugging Tests

```bash
# Debug mode (with Playwright Inspector)
npx playwright test --debug

# Debug specific test
npx playwright test tests/e2e/user-flow.spec.js --debug

# Show trace viewer (after failure)
npx playwright show-trace trace.zip
```

### CI/CD Integration

```yaml
# Example GitHub Actions workflow
name: Playwright Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - name: Install dependencies
        run: npm ci
      - name: Install Playwright Browsers
        run: npx playwright install --with-deps
      - name: Run Playwright tests
        run: npx playwright test
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30
```

---

## Adapting This Pattern to Your Project

### Step 1: Identify User Journeys

Map out the critical paths users take through your application:
- Authentication flow
- Core feature usage
- Data creation/editing workflows
- Navigation patterns

### Step 2: Define Phases

Group related actions into logical phases:
- Phase 1: Authentication (login, register, logout)
- Phase 2: Onboarding (profile setup, first-time user experience)
- Phase 3: Core functionality (main features)
- Phase 4: Advanced features
- Phase 5: Settings and account management

### Step 3: Create Test Data

Build a `test-data.js` file with:
- User credentials
- Sample data for your domain (projects, tasks, items, etc.)
- Common selectors
- Wait times

### Step 4: Set Up Helpers

Create screenshot and utility helpers:
- Screenshot capture functions
- Common assertion helpers
- Navigation helpers

### Step 5: Write Tests Phase by Phase

Start with Phase 1 and build sequentially:
1. Write authentication tests
2. Verify they pass
3. Capture screenshots
4. Move to next phase
5. Use `beforeEach` to ensure required state

### Step 6: Iterate and Refine

- Review screenshots for completeness
- Add edge cases
- Handle error states
- Improve resilience

---

## Troubleshooting Common Issues

### Tests Fail on CI but Pass Locally

**Cause**: Timing differences, viewport size, or missing dependencies

**Solution**:
```javascript
// Add explicit waits
await page.waitForLoadState('networkidle');

// Use CI-specific config
if (process.env.CI) {
  timeout: 60000,  // Longer timeout on CI
}
```

### Screenshots Don't Match Expected

**Cause**: Animations, fonts, or viewport differences

**Solution**:
```javascript
// Disable animations
use: {
  viewport: { width: 1280, height: 720 },
  hasTouch: false,
}

// Wait for fonts to load
await page.waitForLoadState('domcontentloaded');
```

### Tests Are Flaky

**Cause**: Race conditions, timing issues

**Solution**:
```javascript
// Use auto-waiting assertions
await expect(page.locator('h1')).toBeVisible();

// Avoid fixed timeouts
// await page.waitForTimeout(1000);  // Bad

// Use condition-based waiting
await page.waitForSelector('h1', { state: 'visible' });  // Good
```

### State Pollution Between Tests

**Cause**: Tests modifying shared state

**Solution**:
- Use unique test data (random IDs, timestamps)
- Implement cleanup in `afterEach`
- Reset database state before test runs

---

## Additional Resources

- [Playwright Documentation](https://playwright.dev/)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Test Design Patterns](https://playwright.dev/docs/test-patterns)
- [Visual Regression Testing](https://playwright.dev/docs/test-snapshots)

---

## Summary

This testing pattern provides:

✅ **Comprehensive coverage** of user journeys
✅ **Visual documentation** through automated screenshots
✅ **Resilient tests** that handle edge cases
✅ **Maintainable structure** through phases and helpers
✅ **Clear patterns** for common testing scenarios
✅ **Living documentation** that stays in sync with the app

By following this approach, you create tests that not only validate functionality but also serve as documentation and provide debugging context through visual artifacts.
