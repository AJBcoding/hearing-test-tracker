# Playwright E2E Testing Implementation Plan

## Overview

This plan outlines the step-by-step implementation of comprehensive end-to-end testing for the Hearing Test Tracker application using Playwright, based on the patterns documented in `PLAYWRIGHT_TESTING_HANDOFF.md`.

## Goals

- Implement complete user journey testing for the hearing test tracker
- Generate visual documentation through automated screenshots
- Ensure resilient, maintainable test patterns
- Validate core user workflows from authentication through test completion

---

## Phase 1: Project Setup and Configuration

### Task 1.1: Install Playwright Dependencies

**Actions:**
```bash
npm install --save-dev @playwright/test
npx playwright install chromium
```

**Verification:**
- Verify `@playwright/test` is in `package.json` devDependencies
- Confirm Playwright browsers are installed

**Estimated Time:** 5 minutes

---

### Task 1.2: Create Playwright Configuration

**Actions:**
- Create `playwright.config.js` in project root
- Configure for sequential test execution (fullyParallel: false)
- Set up webServer to auto-start dev server
- Configure viewport, timeouts, and reporters

**Configuration Requirements:**
```javascript
- baseURL: Port should match dev server (check vite.config or package.json)
- fullyParallel: false (critical for user flow tests)
- timeout: 30000
- viewport: { width: 1280, height: 720 }
- webServer: Auto-start dev server before tests
- reporter: HTML and list reporters
```

**Files to Create:**
- `/playwright.config.js`

**Verification:**
- Run `npx playwright test --list` to verify config loads
- Verify no configuration errors

**Estimated Time:** 15 minutes

---

### Task 1.3: Create Directory Structure

**Actions:**
- Create directory structure for tests, fixtures, helpers, and screenshots

**Directories to Create:**
```
tests/
├── e2e/
│   ├── fixtures/
│   └── helpers/
docs/
└── screenshots/
    └── flow/
```

**Commands:**
```bash
mkdir -p tests/e2e/fixtures
mkdir -p tests/e2e/helpers
mkdir -p docs/screenshots/flow
```

**Verification:**
- Verify all directories exist
- Check that `docs/screenshots/flow` is ready for screenshot output

**Estimated Time:** 5 minutes

---

## Phase 2: Helper Functions and Test Data

### Task 2.1: Create Screenshot Helper

**Actions:**
- Create `tests/e2e/helpers/screenshot.js`
- Implement `captureStep()` function for standard screenshots
- Implement `captureHover()` function for hover states
- Implement `captureAfterElement()` function for element-specific captures
- Include metadata generation (JSON files alongside screenshots)

**Key Features:**
- Sequential numbering with padding (01, 02, 03, etc.)
- Descriptive filenames
- Metadata tracking (timestamp, URL, viewport, step number)
- Console logging for visibility
- Animations disabled for consistency

**Files to Create:**
- `/tests/e2e/helpers/screenshot.js`

**Verification:**
- Create a simple test that calls `captureStep()` and verify:
  - Screenshot PNG is created in `docs/screenshots/flow/`
  - Metadata JSON is created alongside PNG
  - Console log appears with filename

**Estimated Time:** 20 minutes

---

### Task 2.2: Create Test Data Fixtures

**Actions:**
- Create `tests/e2e/fixtures/test-data.js`
- Define test user credentials
- Define test data for hearing tests
- Define common selectors specific to hearing test tracker
- Define wait times for common scenarios

**Data Structure Needed:**
```javascript
export const testUser = {
  fullName: 'Test User',
  email: 'test.user@example.com',
  password: 'testPassword123'
};

export const testHearingTest = {
  // Define based on actual app requirements
  // Example: testName, date, frequency ranges, etc.
};

export const selectors = {
  // Authentication
  emailInput: 'input[name="email"]',
  passwordInput: 'input[name="password"]',
  // Add app-specific selectors
};

export const waitTimes = {
  shortDelay: 500,
  navigation: 1000,
  apiResponse: 2000,
};
```

**Investigation Required:**
- Review the application to identify:
  - Authentication form selectors
  - Main navigation elements
  - Test creation/management UI elements
  - Test execution UI elements
  - Results viewing elements

**Files to Create:**
- `/tests/e2e/fixtures/test-data.js`

**Verification:**
- Import the file in a test to verify it loads without errors
- Confirm all exported constants are accessible

**Estimated Time:** 30 minutes

---

## Phase 3: User Journey Mapping

### Task 3.1: Map Hearing Test Tracker User Journeys

**Actions:**
- Identify complete user flows through the application
- Document each phase and the steps within

**User Journeys to Map:**

**Phase 1: Authentication**
- Load login page
- View registration form
- Test validation (if applicable)
- Register new user
- Logout
- Login with existing credentials

**Phase 2: Dashboard/Test Management**
- View empty dashboard (first-time user)
- View dashboard with existing tests
- Navigate to create new test
- Create a hearing test
- View test list

**Phase 3: Test Execution**
- Start a hearing test
- Complete test steps (frequency tests, etc.)
- Submit test results
- View completion confirmation

**Phase 4: Results Management**
- View test results list
- Open specific test results
- View detailed results/charts
- Export results (if applicable)
- Navigate back to dashboard

**Phase 5: Additional Features** (if applicable)
- Settings/preferences
- User profile management
- Data management (delete, archive)

**Deliverable:**
- Document the exact flow with numbered steps
- Note any conditional paths (e.g., "if already logged in")
- Identify selectors needed for each step

**Verification:**
- Manually walk through each journey in the app
- Confirm all steps are documented
- Note any edge cases

**Estimated Time:** 45 minutes

---

## Phase 4: Test Implementation - Authentication

### Task 4.1: Create Main Test File Structure

**Actions:**
- Create `tests/e2e/user-flow.spec.js`
- Set up imports (Playwright test, helpers, fixtures)
- Create main test describe block: "Complete User Journey"
- Create Phase 1 describe block: "Authentication"

**Files to Create:**
- `/tests/e2e/user-flow.spec.js`

**Structure:**
```javascript
import { test, expect } from '@playwright/test';
import { captureStep, captureAfterElement } from './helpers/screenshot.js';
import { testUser, selectors, waitTimes } from './fixtures/test-data.js';

test.describe('Complete User Journey', () => {

  test.describe('Phase 1: Authentication', () => {
    // Tests will go here
  });

});
```

**Verification:**
- Run `npx playwright test --list` to verify file is recognized
- Confirm imports work without errors

**Estimated Time:** 10 minutes

---

### Task 4.2: Implement Authentication Tests

**Actions:**
- Implement Test 01: Login page loads correctly
- Implement Test 02: Registration form appears
- Implement Test 03: Registration validation (if applicable)
- Implement Test 04: Successful registration and auto-login
- Implement Test 05: Logout functionality
- Implement Test 06: Login with existing credentials

**Test Pattern:**
Each test should:
1. Navigate to appropriate page
2. Verify expected elements are visible
3. Perform user actions (click, fill, etc.)
4. Assert expected outcome
5. Capture screenshot with appropriate step number

**Resilience Patterns:**
- Test 04: Handle case where user already exists
- Test 06: Handle case where already logged in
- Use `.catch(() => false)` for graceful error handling

**Example Test Structure:**
```javascript
test('01: Login page loads correctly', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('h1')).toBeVisible();
  await expect(page.locator(selectors.emailInput)).toBeVisible();
  await expect(page.locator(selectors.passwordInput)).toBeVisible();
  await captureStep(page, 1, 'login-page');
});
```

**Verification:**
- Run authentication tests: `npx playwright test tests/e2e/user-flow.spec.js`
- Verify all tests pass
- Check that screenshots 01-06 are generated in `docs/screenshots/flow/`
- Review screenshots for visual accuracy

**Estimated Time:** 60 minutes

---

## Phase 5: Test Implementation - Dashboard & Test Management

### Task 5.1: Implement Dashboard Tests

**Actions:**
- Create Phase 2 describe block
- Add `beforeEach` hook to ensure logged-in state
- Implement Test 07: Empty dashboard shows welcome/empty state
- Implement Test 08: Dashboard with existing tests shows test list
- Implement Test 09: Navigate to create test form

**beforeEach Pattern:**
```javascript
test.describe('Phase 2: Test Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');

    const isLoggedIn = await page.locator(selectors.logoutButton)
      .isVisible()
      .catch(() => false);

    if (!isLoggedIn) {
      await page.fill(selectors.emailInput, testUser.email);
      await page.fill(selectors.passwordInput, testUser.password);
      await page.click(selectors.loginButton);
      await page.waitForURL('**/');
    }
  });

  // Tests here...
});
```

**Conditional Path Handling:**
- Test 07 should handle both empty dashboard and dashboard with existing tests
- Use conditional logic to verify appropriate UI state

**Verification:**
- Run Phase 2 tests
- Verify screenshots 07-09 are generated
- Confirm beforeEach successfully logs in for each test

**Estimated Time:** 45 minutes

---

### Task 5.2: Implement Test Creation

**Actions:**
- Implement Test 10: Create test form appears and shows all fields
- Implement Test 11: Fill and submit create test form
- Implement Test 12: Verify test appears in test list
- Implement Test 13: Navigate into newly created test

**Test Pattern:**
- Verify all form fields are visible
- Fill in test data (using fixtures)
- Submit form
- Wait for success confirmation
- Verify redirect/navigation
- Capture screenshots at each major step

**Data to Use:**
```javascript
// From test-data.js
await page.fill(selectors.testNameInput, testHearingTest.name);
// Fill other relevant fields
```

**Verification:**
- Run test creation tests
- Verify screenshots 10-13 capture the complete flow
- Confirm test is actually created in the application

**Estimated Time:** 45 minutes

---

## Phase 6: Test Implementation - Test Execution

### Task 6.1: Implement Test Execution Flow

**Actions:**
- Create Phase 3 describe block: "Test Execution"
- Add `beforeEach` to ensure logged-in state and navigate to test
- Implement Test 14: Test execution page loads
- Implement Test 15: Start test
- Implement Test 16: Complete test steps (frequency tests, etc.)
- Implement Test 17: Submit test results
- Implement Test 18: View completion confirmation

**Complexity Note:**
The test execution flow may be complex depending on:
- Number of steps in a hearing test
- Interactive elements (audio playback, user responses)
- Timing/sequencing requirements

**Approach:**
- Break down test execution into discrete steps
- Capture screenshots at each major milestone
- Handle any audio/media elements appropriately
- Ensure proper waiting for async operations

**Special Considerations:**
```javascript
// If audio playback is involved
await page.waitForTimeout(waitTimes.audioPlayback);

// If user needs to respond to stimuli
await page.click(selectors.responseButton);

// Wait for test step completion
await page.waitForSelector(selectors.nextStepButton, { state: 'visible' });
```

**Verification:**
- Run test execution tests
- Verify complete flow from start to finish
- Check screenshots 14-18 capture all major steps
- Confirm test results are properly saved

**Estimated Time:** 90 minutes

---

## Phase 7: Test Implementation - Results Management

### Task 7.1: Implement Results Viewing

**Actions:**
- Create Phase 4 describe block: "Results Management"
- Add `beforeEach` for logged-in state
- Implement Test 19: Navigate to results list
- Implement Test 20: View test results list
- Implement Test 21: Open specific test result
- Implement Test 22: View detailed results (charts, data)
- Implement Test 23: Navigate back to dashboard

**Focus Areas:**
- Verify results data is displayed correctly
- Check for charts/visualizations
- Test navigation between results views
- Verify data persistence

**Screenshot Strategy:**
- Capture results list view
- Capture detailed results view
- Capture any charts/visualizations
- Capture navigation states

**Verification:**
- Run results management tests
- Verify screenshots 19-23 are generated
- Review results display for accuracy
- Confirm navigation works correctly

**Estimated Time:** 60 minutes

---

## Phase 8: Additional Features (If Applicable)

### Task 8.1: Implement Settings/Profile Tests

**Actions (if applicable):**
- Create Phase 5 describe block: "Settings & Profile"
- Add `beforeEach` for logged-in state
- Implement tests for:
  - View user profile
  - Edit user settings
  - Update preferences
  - Save changes

**Conditional:**
Only implement if the application has settings/profile features

**Estimated Time:** 30-45 minutes (if applicable)

---

### Task 8.2: Implement Data Management Tests

**Actions (if applicable):**
- Extend results management phase or create new phase
- Implement tests for:
  - Delete test
  - Archive test
  - Export test results
  - Bulk operations (if applicable)

**Conditional:**
Only implement if the application has these features

**Estimated Time:** 30-45 minutes (if applicable)

---

## Phase 9: Refinement and Edge Cases

### Task 9.1: Add Error Handling Tests

**Actions:**
- Add tests for validation errors:
  - Invalid login credentials
  - Invalid form inputs
  - Network errors (if testable)
- Verify error messages display correctly
- Capture screenshots of error states

**Pattern:**
```javascript
test('Registration validation shows errors', async ({ page }) => {
  await page.goto('/');
  await page.click(selectors.registerTab);

  // Submit empty form
  await page.click(selectors.registerButton);

  // Verify validation errors
  await expect(page.locator(selectors.errorMessage)).toBeVisible();
  await captureStep(page, XX, 'registration-validation-errors');
});
```

**Verification:**
- Run error handling tests
- Verify error states are properly captured
- Confirm error messages match expected behavior

**Estimated Time:** 45 minutes

---

### Task 9.2: Improve Test Resilience

**Actions:**
- Review all tests for potential flakiness
- Add appropriate waits where needed
- Replace `waitForTimeout` with condition-based waits where possible
- Handle race conditions

**Patterns to Apply:**
```javascript
// Replace
await page.waitForTimeout(2000);

// With
await page.waitForLoadState('networkidle');
// or
await expect(page.locator(selector)).toBeVisible();
```

**Review Checklist:**
- [ ] All page navigations have `waitForURL` or element verification
- [ ] Form submissions have success/error verification
- [ ] Dynamic content has explicit wait conditions
- [ ] No arbitrary timeouts unless necessary (animations, media)

**Verification:**
- Run full test suite 3 times consecutively
- Verify consistent pass rate
- Identify and fix any flaky tests

**Estimated Time:** 45 minutes

---

### Task 9.3: Refactor Common Patterns

**Actions:**
- Identify repeated code across tests
- Extract to helper functions
- Create navigation helpers if needed
- Create assertion helpers if needed

**Example Helper:**
```javascript
// In helpers/navigation.js
export async function ensureLoggedIn(page, user) {
  await page.goto('/');

  const isLoggedIn = await page.locator(selectors.logoutButton)
    .isVisible()
    .catch(() => false);

  if (!isLoggedIn) {
    await page.fill(selectors.emailInput, user.email);
    await page.fill(selectors.passwordInput, user.password);
    await page.click(selectors.loginButton);
    await page.waitForURL('**/');
  }
}
```

**Verification:**
- Run full test suite after refactoring
- Verify all tests still pass
- Confirm code is more maintainable

**Estimated Time:** 30 minutes

---

## Phase 10: Documentation and CI/CD

### Task 10.1: Update package.json Scripts

**Actions:**
- Add test scripts to `package.json`

**Scripts to Add:**
```json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:headed": "playwright test --headed",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:debug": "playwright test --debug",
    "test:e2e:report": "playwright show-report"
  }
}
```

**Verification:**
- Run each script to verify it works
- Confirm reports are generated correctly

**Estimated Time:** 10 minutes

---

### Task 10.2: Create Test Documentation

**Actions:**
- Create `tests/e2e/README.md`
- Document how to run tests
- Explain test organization
- Provide troubleshooting tips
- Link to generated screenshots

**Content to Include:**
- Quick start guide
- Test structure explanation
- How to add new tests
- How to debug failures
- Screenshot location and usage

**Files to Create:**
- `/tests/e2e/README.md`

**Verification:**
- Follow documentation as a new developer would
- Verify all instructions are clear and accurate

**Estimated Time:** 30 minutes

---

### Task 10.3: Set Up CI/CD Integration (Optional)

**Actions (if using GitHub Actions):**
- Create `.github/workflows/playwright.yml`
- Configure to run on push/PR
- Set up artifact upload for reports and screenshots
- Configure proper Node.js version and caching

**GitHub Actions Template:**
```yaml
name: Playwright Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
          cache: 'npm'
      - name: Install dependencies
        run: npm ci
      - name: Install Playwright Browsers
        run: npx playwright install --with-deps
      - name: Run Playwright tests
        run: npm run test:e2e
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-screenshots
          path: docs/screenshots/
          retention-days: 30
```

**Verification:**
- Push to repository and verify action runs
- Check that artifacts are uploaded
- Verify tests pass in CI environment

**Estimated Time:** 30 minutes (if implementing CI/CD)

---

## Phase 11: Final Verification

### Task 11.1: Full Test Suite Execution

**Actions:**
- Run complete test suite from scratch
- Verify all tests pass
- Review all generated screenshots
- Check HTML report for completeness

**Commands:**
```bash
# Clean previous test artifacts
rm -rf docs/screenshots/flow/*
rm -rf playwright-report/

# Run full suite
npm run test:e2e

# View report
npm run test:e2e:report
```

**Verification Checklist:**
- [ ] All tests pass (100% pass rate)
- [ ] Screenshots are generated for all steps
- [ ] Screenshot metadata (JSON files) are present
- [ ] HTML report is comprehensive and readable
- [ ] No warnings or errors in console output
- [ ] Test execution time is reasonable

**Estimated Time:** 30 minutes

---

### Task 11.2: Code Review and Quality Check

**Actions:**
- Review all test code for quality
- Ensure consistent style
- Verify meaningful test names
- Check for code duplication
- Validate error handling

**Quality Checklist:**
- [ ] Test names clearly describe what is being tested
- [ ] Selectors are semantic, not brittle
- [ ] Common patterns are extracted to helpers
- [ ] Test data is centralized in fixtures
- [ ] Error cases are handled gracefully
- [ ] Comments explain non-obvious patterns
- [ ] No hardcoded values (use fixtures)

**Verification:**
- Conduct peer review if possible
- Run linter if configured

**Estimated Time:** 30 minutes

---

### Task 11.3: Documentation Review

**Actions:**
- Review all documentation
- Ensure README is complete
- Verify screenshots are organized
- Check that handoff document is referenced
- Update main project README with testing information

**Documentation to Review:**
- `/tests/e2e/README.md`
- `/docs/PLAYWRIGHT_TESTING_HANDOFF.md`
- `/docs/PLAYWRIGHT_IMPLEMENTATION_PLAN.md` (this document)
- Project root README (add testing section)

**Verification:**
- All links work
- Instructions are clear
- Examples are accurate

**Estimated Time:** 20 minutes

---

## Summary

### Total Estimated Time
- **Phase 1**: 25 minutes (Setup)
- **Phase 2**: 50 minutes (Helpers & Fixtures)
- **Phase 3**: 45 minutes (Journey Mapping)
- **Phase 4**: 70 minutes (Authentication Tests)
- **Phase 5**: 90 minutes (Dashboard & Test Management)
- **Phase 6**: 90 minutes (Test Execution)
- **Phase 7**: 60 minutes (Results Management)
- **Phase 8**: 60 minutes (Additional Features - if applicable)
- **Phase 9**: 120 minutes (Refinement)
- **Phase 10**: 70 minutes (Documentation & CI/CD)
- **Phase 11**: 80 minutes (Final Verification)

**Total: ~12-14 hours** (depending on application complexity and optional features)

### Key Deliverables

1. **Configuration**
   - `playwright.config.js`

2. **Test Infrastructure**
   - `tests/e2e/helpers/screenshot.js`
   - `tests/e2e/fixtures/test-data.js`

3. **Test Suite**
   - `tests/e2e/user-flow.spec.js`

4. **Documentation**
   - `tests/e2e/README.md`
   - Updated project README

5. **Visual Documentation**
   - `docs/screenshots/flow/` (with numbered screenshots and metadata)

6. **CI/CD** (optional)
   - `.github/workflows/playwright.yml`

### Success Criteria

✅ Complete user journey is tested from authentication to results viewing
✅ All tests pass consistently
✅ Screenshots document every major step
✅ Tests are resilient and handle edge cases
✅ Code is maintainable with helpers and fixtures
✅ Documentation is clear and comprehensive
✅ CI/CD pipeline runs tests automatically (if implemented)

### Next Steps After Implementation

1. **Integrate into Development Workflow**
   - Run tests before merging PRs
   - Use screenshots for UI reviews
   - Monitor for flaky tests

2. **Expand Coverage**
   - Add more edge cases as discovered
   - Add accessibility tests
   - Add performance tests if needed

3. **Maintain**
   - Update tests when features change
   - Keep selectors up to date
   - Review and update test data
   - Monitor screenshot diff for unintended changes

---

## Appendix: Application-Specific Considerations

### Hearing Test Tracker Specific Notes

Before implementation, investigate and document:

1. **Authentication System**
   - Does it use Supabase Auth?
   - What are the exact selectors for login/register forms?
   - Is there email verification?

2. **Test Structure**
   - What types of hearing tests exist?
   - What data is collected during a test?
   - How are results stored and displayed?

3. **User Workflows**
   - Can users create multiple tests?
   - Can users retake tests?
   - Is there test scheduling?

4. **Data Model**
   - What constitutes a "test"?
   - What are the test parameters?
   - How are results structured?

5. **Special UI Elements**
   - Audio playback controls
   - Frequency sliders or controls
   - Result charts/graphs
   - Any custom interactive elements

### Investigation Tasks (Before Starting Implementation)

- [ ] Review application routes and navigation
- [ ] Identify all form elements and their selectors
- [ ] Map out the complete user journey manually
- [ ] Note any async operations or delays
- [ ] Identify any third-party integrations (e.g., Supabase)
- [ ] Check for any existing test setup or configuration

This investigation will inform the actual test data and selectors used in the implementation.
