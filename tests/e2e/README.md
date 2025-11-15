# Playwright E2E Tests

## Overview

This directory contains end-to-end (E2E) tests for the Hearing Test Tracker application using Playwright. These tests validate complete user journeys through the application, from dashboard navigation to test uploads and result viewing.

## Project Status

### Completed

✅ Playwright test framework installed and configured
✅ Test directory structure created
✅ Screenshot helper utilities implemented
✅ Test data fixtures created with selectors and routes
✅ Comprehensive test suite covering 11 test scenarios across 5 phases
✅ Package.json scripts for running tests
✅ Sequential test execution configured
✅ Auto-start dev server integration

### Current Limitations

⚠️ **Backend API Required**: The tests currently fail because the backend API server (port 5001) is not running. The frontend makes API calls to `/api/tests` which are proxied to `localhost:5001`, but this service is not available.

**To run these tests successfully, you need:**
1. Start the backend API server on port 5001
2. Ensure the API endpoints are functional (`GET /api/tests`, etc.)
3. Have a database configured and accessible

## Test Structure

The test suite is organized into 5 phases that cover the complete user journey:

### Phase 1: Dashboard (Empty State)
- Test 01: Home page redirects to dashboard
- Test 02: Empty dashboard shows welcome message
- Test 03: Navigation bar is visible and functional

### Phase 2: Upload Test
- Test 04: Navigate to upload page from dashboard
- Test 05: Upload page shows form with file input
- Test 06: Process button is disabled without file

### Phase 3: Dashboard with Tests
- Test 07: Navigate back to dashboard
- Test 08: Dashboard shows test statistics (if tests exist)

### Phase 4: Test List
- Test 09: Navigate to all tests page
- Test 10: Test list page shows table or empty state

### Phase 5: Test Viewer
- Test 11: View test details (if tests exist)

## Directory Structure

```
tests/e2e/
├── fixtures/
│   └── test-data.js         # Centralized test data, selectors, and routes
├── helpers/
│   └── screenshot.js        # Screenshot capture utilities
├── user-flow.spec.js        # Main test suite
└── README.md                # This file

docs/screenshots/flow/       # Auto-generated screenshots (created during test runs)
```

## Running Tests

### Prerequisites

1. Install dependencies:
   ```bash
   npm install
   cd frontend && npm install
   ```

2. **Start the backend API server** (required for tests to pass):
   ```bash
   # Start your backend server on port 5001
   # Example:
   cd backend && npm start
   ```

### Test Commands

From the project root directory:

```bash
# Run all tests (headless)
npm run test:e2e

# Run tests in headed mode (see browser)
npm run test:e2e:headed

# Run tests in UI mode (interactive)
npm run test:e2e:ui

# Run tests in debug mode
npm run test:e2e:debug

# View test report (after running tests)
npm run test:e2e:report
```

## Configuration

The Playwright configuration is in `/playwright.config.js`:

- **Base URL**: `http://localhost:3000` (frontend dev server)
- **Test Directory**: `./tests/e2e`
- **Execution Mode**: Sequential (`fullyParallel: false`)
- **Timeout**: 30 seconds per test
- **Viewport**: 1280x720 (consistent screenshots)
- **Web Server**: Auto-starts frontend dev server
- **Reporters**: HTML report + list output

## Test Data

Test data, selectors, and expected values are centralized in `fixtures/test-data.js`:

```javascript
import { selectors, routes, expectedValues } from './fixtures/test-data.js';

// Use in tests
await page.click(selectors.navDashboard);
await page.goto(routes.upload);
```

### Key Selectors

- **Navigation**: `navDashboard`, `navUpload`, `navTests`
- **Dashboard**: `dashboardTitle`, `totalTestsCard`, `uploadTestButton`
- **Upload**: `fileInput`, `processButton`, `uploadPageTitle`
- **Tests**: `testListTable`, `viewTestButton`

## Screenshot Documentation

The test suite automatically captures screenshots at key moments using the `captureStep()` helper:

```javascript
import { captureStep } from './helpers/screenshot.js';

// Capture screenshot with sequential numbering
await captureStep(page, 1, 'login-page');
```

**Screenshot Features:**
- Sequential numbering (01, 02, 03, etc.)
- Descriptive filenames (`01-login-page.png`)
- Metadata JSON files (`01-login-page.json`)
- Full-page screenshots with animations disabled
- Saved to `docs/screenshots/flow/`

**Screenshot Metadata Example:**
```json
{
  "description": "dashboard-empty-state",
  "timestamp": "2025-11-15",
  "url": "http://localhost:3000/dashboard",
  "viewport": { "width": 1280, "height": 720 },
  "stepNumber": 2
}
```

## Writing New Tests

### Basic Test Pattern

```javascript
test('Description of what test validates', async ({ page }) => {
  // 1. Navigate to page
  await page.goto('/dashboard');

  // 2. Perform actions
  await page.click(selectors.navUpload);

  // 3. Verify expected state
  await expect(page.locator(selectors.uploadPageTitle)).toBeVisible();

  // 4. Capture screenshot
  await captureStep(page, stepNumber, 'descriptive-name');
});
```

### Best Practices

1. **Use Semantic Selectors**
   ```javascript
   // Good
   page.locator('button:has-text("Upload")');

   // Avoid
   page.locator('.btn-123');
   ```

2. **Use Auto-Waiting**
   ```javascript
   // Playwright waits automatically
   await expect(page.locator('h1')).toBeVisible();

   // Avoid fixed timeouts when possible
   await page.waitForTimeout(1000); // Only for animations
   ```

3. **Handle Conditional States**
   ```javascript
   const isEmpty = await page.locator('.empty-state')
     .isVisible()
     .catch(() => false);

   if (isEmpty) {
     // Handle empty state
   } else {
     // Handle populated state
   }
   ```

4. **Centralize Test Data**
   - Add new selectors to `fixtures/test-data.js`
   - Don't hardcode selectors in tests

## Debugging Tests

### View Test Traces

When tests fail, Playwright captures traces:

```bash
npx playwright show-trace test-results/path-to-trace.zip
```

### Run Specific Tests

```bash
# Run single test file
npx playwright test user-flow.spec.js

# Run tests matching a pattern
npx playwright test --grep "Dashboard"

# Run in debug mode with inspector
npx playwright test --debug
```

### Common Issues

**Issue**: Tests timeout waiting for `networkidle`
**Cause**: API requests are failing (backend not running)
**Solution**: Start the backend API server

**Issue**: Elements not found
**Cause**: Selector may be incorrect or page not fully loaded
**Solution**: Check selector in `test-data.js`, ensure page loads properly

**Issue**: Target crashed
**Cause**: Browser page encountered an error
**Solution**: Check browser console, verify API responses

## CI/CD Integration

To run tests in CI/CD (GitHub Actions example):

```yaml
name: Playwright Tests

on: [push, pull_request]

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
      - name: Install frontend dependencies
        run: cd frontend && npm ci
      - name: Install Playwright Browsers
        run: npx playwright install --with-deps
      - name: Start backend server
        run: # Add command to start backend
      - name: Run Playwright tests
        run: npm run test:e2e
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
```

## Future Enhancements

### Planned Test Coverage

- [ ] **Upload Flow**: Test actual file upload with sample audiogram
- [ ] **Test Editing**: Validate test review/edit functionality
- [ ] **Bulk Upload**: Test bulk upload feature
- [ ] **Error Handling**: Test validation errors and API failures
- [ ] **Results Viewing**: Detailed test result visualization
- [ ] **Charts/Graphs**: Verify audiogram charts render correctly
- [ ] **Navigation Flow**: Complete navigation between all pages
- [ ] **Accessibility**: Add a11y tests using @axe-core/playwright

### Additional Features to Add

- Visual regression testing (screenshot comparison)
- API mocking for frontend-only testing
- Performance testing
- Mobile viewport testing
- Cross-browser testing (Firefox, Safari)

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Test Design Patterns](https://playwright.dev/docs/test-patterns)
- [Implementation Plan](../../docs/PLAYWRIGHT_IMPLEMENTATION_PLAN.md)
- [Testing Handoff](../../docs/PLAYWRIGHT_TESTING_HANDOFF.md)

## Getting Help

If you encounter issues:

1. Check the test traces: `npm run test:e2e:report`
2. Run in debug mode: `npm run test:e2e:debug`
3. Verify backend API is running on port 5001
4. Check browser console for errors
5. Review the implementation plan for guidance

## Summary

This Playwright test suite provides comprehensive E2E coverage of the Hearing Test Tracker application. While currently requiring a backend API to function, the infrastructure is fully set up and ready to validate user workflows once the API is available.

**Key Deliverables:**
- ✅ 11 test scenarios across 5 user journey phases
- ✅ Automated screenshot documentation
- ✅ Centralized test data management
- ✅ Helper utilities for reusable patterns
- ✅ Sequential test execution for user flows
- ✅ Comprehensive configuration and documentation
