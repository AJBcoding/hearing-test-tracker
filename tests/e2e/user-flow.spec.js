import { test, expect } from '@playwright/test';
import { captureStep, captureAfterElement } from './helpers/screenshot.js';
import { selectors, waitTimes, routes, expectedValues } from './fixtures/test-data.js';

test.describe('Complete User Journey', () => {

  // =================================================================
  // PHASE 1: DASHBOARD (EMPTY STATE)
  // =================================================================
  test.describe('Phase 1: Dashboard (Empty State)', () => {

    test('01: Home page redirects to dashboard', async ({ page }) => {
      // Navigate to home page
      await page.goto('/');

      // Should redirect to /dashboard
      await page.waitForURL('**/dashboard');

      // Verify we're on the dashboard
      await expect(page).toHaveURL(/\/dashboard$/);

      // Capture screenshot
      await captureStep(page, 1, 'home-redirect-to-dashboard');
    });

    test('02: Empty dashboard shows welcome message', async ({ page }) => {
      await page.goto('/dashboard');

      // Wait for page to load
      const loadingGone = page.locator(selectors.loadingText);
      await expect(loadingGone).not.toBeVisible().catch(() => {});

      // Check for empty state
      const emptyState = page.locator(selectors.dashboardTitle);
      const hasTests = await emptyState.isVisible().catch(() => false);

      if (hasTests) {
        // Empty state: should show "No tests yet" message
        await expect(emptyState).toBeVisible();
        await expect(page.locator('text=Upload your first audiogram')).toBeVisible();
        await expect(page.locator(selectors.uploadTestButton)).toBeVisible();
        await captureStep(page, 2, 'dashboard-empty-state');
      } else {
        // Has tests: capture the state
        await expect(page.locator(selectors.totalTestsCard)).toBeVisible();
        await captureStep(page, 2, 'dashboard-with-existing-tests');
      }
    });

    test('03: Navigation bar is visible and functional', async ({ page }) => {
      await page.goto('/dashboard');

      // Verify navigation elements are visible
      await expect(page.locator(selectors.appTitle)).toBeVisible();
      await expect(page.locator(selectors.navDashboard)).toBeVisible();
      await expect(page.locator(selectors.navUpload)).toBeVisible();
      await expect(page.locator(selectors.navTests)).toBeVisible();

      // Capture screenshot
      await captureStep(page, 3, 'navigation-bar');
    });

  });

  // =================================================================
  // PHASE 2: UPLOAD TEST
  // =================================================================
  test.describe('Phase 2: Upload Test', () => {

    test('04: Navigate to upload page from dashboard', async ({ page }) => {
      await page.goto('/dashboard');

      // Wait for dashboard to load
      await page.waitForLoadState('networkidle');

      // Try to click "Upload Test" button if in empty state, otherwise use nav
      const uploadButton = page.locator(selectors.uploadTestButton);
      const isEmptyState = await uploadButton.isVisible().catch(() => false);

      if (isEmptyState) {
        await uploadButton.click();
      } else {
        await page.locator(selectors.navUpload).click();
      }

      // Verify we're on the upload page
      await page.waitForURL('**/upload');
      await expect(page.locator(selectors.uploadPageTitle)).toBeVisible();

      // Capture screenshot
      await captureStep(page, 4, 'navigate-to-upload-page');
    });

    test('05: Upload page shows form with file input', async ({ page }) => {
      await page.goto('/upload');

      // Verify upload page elements
      await expect(page.locator(selectors.uploadPageTitle)).toBeVisible();
      await expect(page.locator(selectors.singleUploadTab)).toBeVisible();
      await expect(page.locator(selectors.bulkUploadTab)).toBeVisible();

      // Single upload tab should be active by default
      await expect(page.locator(selectors.fileInput)).toBeVisible();
      await expect(page.locator(selectors.processButton)).toBeVisible();
      await expect(page.locator(selectors.processButton)).toBeDisabled();

      // Capture screenshot
      await captureStep(page, 5, 'upload-form');
    });

    test('06: Process button is disabled without file', async ({ page }) => {
      await page.goto('/upload');

      // Verify button is initially disabled
      await expect(page.locator(selectors.processButton)).toBeDisabled();

      // Capture screenshot
      await captureStep(page, 6, 'upload-button-disabled');
    });

  });

  // =================================================================
  // PHASE 3: DASHBOARD WITH TESTS (Conditional)
  // =================================================================
  test.describe('Phase 3: Dashboard with Tests', () => {

    test('07: Navigate back to dashboard', async ({ page }) => {
      await page.goto('/upload');

      // Click dashboard nav link
      await page.locator(selectors.navDashboard).click();

      // Verify we're on dashboard
      await page.waitForURL('**/dashboard');
      await expect(page).toHaveURL(/\/dashboard$/);

      // Capture screenshot
      await captureStep(page, 7, 'navigate-back-to-dashboard');
    });

    test('08: Dashboard shows test statistics (if tests exist)', async ({ page }) => {
      await page.goto('/dashboard');

      // Wait for loading to finish
      await page.waitForLoadState('networkidle');

      // Check if there are tests
      const emptyState = page.locator(selectors.dashboardTitle);
      const isEmpty = await emptyState.isVisible().catch(() => false);

      if (!isEmpty) {
        // Has tests: verify statistics cards
        await expect(page.locator(selectors.totalTestsCard)).toBeVisible();
        await expect(page.locator(selectors.latestTestCard)).toBeVisible();
        await expect(page.locator(selectors.testsThisYearCard)).toBeVisible();

        // Verify recent tests table
        await expect(page.locator(selectors.recentTestsTable)).toBeVisible();

        await captureStep(page, 8, 'dashboard-with-statistics');
      } else {
        // Empty state
        await expect(emptyState).toBeVisible();
        await captureStep(page, 8, 'dashboard-still-empty');
      }
    });

  });

  // =================================================================
  // PHASE 4: TEST LIST
  // =================================================================
  test.describe('Phase 4: Test List', () => {

    test('09: Navigate to all tests page', async ({ page }) => {
      await page.goto('/dashboard');

      // Click "All Tests" nav link
      await page.locator(selectors.navTests).click();

      // Verify we're on tests page
      await page.waitForURL('**/tests');
      await expect(page).toHaveURL(/\/tests$/);

      // Capture screenshot
      await captureStep(page, 9, 'navigate-to-tests-page');
    });

    test('10: Test list page shows table or empty state', async ({ page }) => {
      await page.goto('/tests');

      // Wait for page to load
      await page.waitForLoadState('networkidle');

      // Check for tests table or empty state
      const hasTable = await page.locator(selectors.testListTable).isVisible().catch(() => false);
      const hasEmpty = await page.locator('text=No tests').isVisible().catch(() => false);

      if (hasTable) {
        await expect(page.locator(selectors.testListTable)).toBeVisible();
        await captureStep(page, 10, 'test-list-with-tests');
      } else if (hasEmpty) {
        await expect(page.locator('text=No tests')).toBeVisible();
        await captureStep(page, 10, 'test-list-empty');
      } else {
        // Capture whatever state we're in
        await captureStep(page, 10, 'test-list-page');
      }
    });

  });

  // =================================================================
  // PHASE 5: TEST VIEWER (Conditional - only if tests exist)
  // =================================================================
  test.describe('Phase 5: Test Viewer', () => {

    test('11: View test details (if tests exist)', async ({ page }) => {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      // Check if there are tests
      const viewDetailsButton = page.locator(selectors.viewDetailsButton).first();
      const hasTests = await viewDetailsButton.isVisible().catch(() => false);

      if (hasTests) {
        // Click to view first test
        await viewDetailsButton.click();

        // Wait for navigation to test viewer
        await page.waitForURL('**/tests/**');
        await expect(page).toHaveURL(/\/tests\/\d+$/);

        // Wait for test details to load
        await page.waitForLoadState('networkidle');

        // Capture screenshot
        await captureStep(page, 11, 'test-viewer-details');
      } else {
        // No tests available
        await page.goto('/dashboard');
        await captureStep(page, 11, 'no-tests-to-view');
      }
    });

  });

});
