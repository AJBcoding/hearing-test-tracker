import { test, expect } from '@playwright/test';

/**
 * Navigation & UI Implementation Tests
 * Tests all features from the Navigation & UI handoff implementation
 */

// Test configuration
const BASE_URL = 'http://localhost:3001';
const TEST_ID = 'ede987c0-9b86-4ee4-8658-4ac3e90bfe6c'; // Existing test in database

test.describe('Navigation & UI Implementation', () => {

  // =================================================================
  // Test 1: Navigation Bar
  // =================================================================
  test('01: Navigation bar displays correctly', async ({ page }) => {
    await page.goto(BASE_URL);

    // Verify title
    await expect(page.getByText('Hearing Test Tracker')).toBeVisible();

    // Verify navigation links exist
    await expect(page.getByRole('link', { name: 'Dashboard' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Upload Test' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'All Tests' })).toBeVisible();
  });

  test('02: Navigation links work', async ({ page }) => {
    await page.goto(BASE_URL);

    // Click Dashboard
    await page.getByRole('link', { name: 'Dashboard' }).click();
    await expect(page).toHaveURL(/\/dashboard/);

    // Click Upload Test
    await page.getByRole('link', { name: 'Upload Test' }).click();
    await expect(page).toHaveURL(/\/upload/);

    // Click All Tests
    await page.getByRole('link', { name: 'All Tests' }).click();
    await expect(page).toHaveURL(/\/tests$/);
  });

  // =================================================================
  // Test 2: Dashboard
  // =================================================================
  test('03: Dashboard displays stat cards', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);

    // Wait for data to load
    await page.waitForTimeout(1000);

    // Verify stat cards exist - use more specific selectors
    await expect(page.getByText('Total Tests').first()).toBeVisible();
    await expect(page.getByText('Latest Test').first()).toBeVisible();
    await expect(page.getByText('Tests This Year')).toBeVisible();
  });

  test('04: Dashboard shows latest test card', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);

    // Wait for data to load
    await page.waitForTimeout(1000);

    // Check for Latest Test section
    const latestTestHeading = page.getByRole('heading', { name: 'Latest Test' });
    if (await latestTestHeading.isVisible()) {
      // Verify confidence badge exists
      const confidenceBadge = page.locator('text=/\\d+% confidence/');
      await expect(confidenceBadge).toBeVisible();

      // Verify View Details button
      await expect(page.getByRole('button', { name: 'View Details' })).toBeVisible();
    }
  });

  test('05: Dashboard shows recent tests table', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);

    // Wait for data to load and table to render
    await page.waitForTimeout(2000);

    // Verify Recent Tests section
    await expect(page.getByRole('heading', { name: 'Recent Tests' })).toBeVisible();

    // Verify table exists with data
    const table = page.locator('table').last();
    await expect(table).toBeVisible();

    // Verify we have table cells (data loaded)
    const tableCells = table.locator('td');
    await expect(tableCells.first()).toBeVisible();
  });

  // =================================================================
  // Test 3: All Tests Page
  // =================================================================
  test('06: All Tests page displays correctly', async ({ page }) => {
    await page.goto(`${BASE_URL}/tests`);

    // Wait for data to load
    await page.waitForTimeout(2000);

    // Verify page title
    await expect(page.getByRole('heading', { name: 'All Tests' })).toBeVisible();

    // Verify page description shows count
    await expect(page.getByText(/Showing \d+ test/)).toBeVisible();

    // Verify table exists with data
    const table = page.locator('table');
    await expect(table).toBeVisible();

    // Verify confidence badge (indicates data loaded)
    await expect(page.locator('text=/\\d+%/')).toBeVisible();
  });

  test('07: All Tests table shows data', async ({ page }) => {
    await page.goto(`${BASE_URL}/tests`);

    // Wait for data to load
    await page.waitForTimeout(1000);

    // Verify at least one test row exists
    const tableRows = page.locator('tbody tr');
    await expect(tableRows).toHaveCount(1); // We know there's 1 test

    // Verify confidence badge
    await expect(page.locator('text=/\\d+%/')).toBeVisible();
  });

  test('08: Clicking table row navigates to test viewer', async ({ page }) => {
    await page.goto(`${BASE_URL}/tests`);

    // Wait for data to load
    await page.waitForTimeout(1000);

    // Click first table row
    await page.locator('tbody tr').first().click();

    // Should navigate to test viewer
    await expect(page).toHaveURL(/\/tests\/[a-f0-9-]+$/);
  });

  // =================================================================
  // Test 4: Test Viewer
  // =================================================================
  test('09: Test viewer displays test information', async ({ page }) => {
    await page.goto(`${BASE_URL}/tests/${TEST_ID}`);

    // Wait for data to load
    await page.waitForTimeout(1000);

    // Verify test information card
    await expect(page.getByRole('heading', { name: 'Test Information' })).toBeVisible();

    // Verify buttons
    await expect(page.getByRole('button', { name: 'Edit Test Data' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Delete Test' })).toBeVisible();

    // Verify confidence badge
    await expect(page.locator('text=/\\d+% confidence/')).toBeVisible();
  });

  test('10: Test viewer displays audiogram chart', async ({ page }) => {
    await page.goto(`${BASE_URL}/tests/${TEST_ID}`);

    // Wait for data to load
    await page.waitForTimeout(1000);

    // Verify Audiogram section
    await expect(page.getByRole('heading', { name: 'Audiogram' })).toBeVisible();

    // Check for chart SVG (Recharts renders as SVG)
    const chartSvg = page.locator('svg').first();
    await expect(chartSvg).toBeVisible();
  });

  test('11: Test viewer displays measurements tabs', async ({ page }) => {
    await page.goto(`${BASE_URL}/tests/${TEST_ID}`);

    // Wait for data to load
    await page.waitForTimeout(1000);

    // Verify Measurements section
    await expect(page.getByRole('heading', { name: 'Measurements' })).toBeVisible();

    // Verify tabs exist and can be clicked
    const leftTab = page.getByRole('tab', { name: 'Left Ear' });
    const rightTab = page.getByRole('tab', { name: 'Right Ear' });

    await expect(leftTab).toBeVisible();
    await expect(rightTab).toBeVisible();

    // Click Right Ear tab
    await rightTab.click();
    await page.waitForTimeout(500);

    // Verify Right Ear tab is now active
    await expect(rightTab).toHaveAttribute('aria-selected', 'true');

    // Verify measurement table exists and has data (check for dB values)
    const measurements = page.locator('td').filter({ hasText: /\d+\.\d+/ });
    await expect(measurements.first()).toBeVisible();
  });

  // =================================================================
  // Test 5: Review/Edit Page
  // =================================================================
  test('12: Review/Edit page displays correctly', async ({ page }) => {
    await page.goto(`${BASE_URL}/tests/${TEST_ID}/review`);

    // Wait for data to load
    await page.waitForTimeout(1000);

    // Verify page title
    await expect(page.getByRole('heading', { name: 'Review & Edit Test' })).toBeVisible();

    // Verify confidence badge
    await expect(page.locator('text=/\\d+% confidence/')).toBeVisible();
  });

  test('13: Review/Edit page has editable form', async ({ page }) => {
    await page.goto(`${BASE_URL}/tests/${TEST_ID}/review`);

    // Wait for data to load
    await page.waitForTimeout(1000);

    // Verify form fields exist
    await expect(page.getByText('Test Metadata')).toBeVisible();
    await expect(page.getByLabel('Location')).toBeVisible();
    await expect(page.getByLabel('Device')).toBeVisible();

    // Verify action buttons
    await expect(page.getByRole('button', { name: 'Cancel' })).toBeVisible();
    await expect(page.getByRole('button', { name: /Accept.*Save/ })).toBeVisible();
  });

  test('14: Review/Edit page has audiogram data tabs', async ({ page }) => {
    await page.goto(`${BASE_URL}/tests/${TEST_ID}/review`);

    // Wait for data to load
    await page.waitForTimeout(1000);

    // Verify Audiogram Data section
    await expect(page.getByText('Audiogram Data')).toBeVisible();

    // Verify tabs
    await expect(page.getByRole('tab', { name: 'Left Ear' })).toBeVisible();
    await expect(page.getByRole('tab', { name: 'Right Ear' })).toBeVisible();
  });

  test('15: Cancel button returns to test viewer', async ({ page }) => {
    await page.goto(`${BASE_URL}/tests/${TEST_ID}/review`);

    // Wait for data to load
    await page.waitForTimeout(1000);

    // Click Cancel button
    await page.getByRole('button', { name: 'Cancel' }).click();

    // Should navigate back to test viewer
    await expect(page).toHaveURL(`${BASE_URL}/tests/${TEST_ID}`);
  });

  // =================================================================
  // Test 6: Upload Page
  // =================================================================
  test('16: Upload page displays correctly', async ({ page }) => {
    await page.goto(`${BASE_URL}/upload`);

    // Verify page title
    await expect(page.getByRole('heading', { name: 'Upload Hearing Test' })).toBeVisible();

    // Verify upload tabs exist
    await expect(page.getByRole('tab', { name: 'Single Upload' })).toBeVisible();
    await expect(page.getByRole('tab', { name: 'Bulk Upload' })).toBeVisible();

    // Verify upload form is visible (Single Upload is default)
    await expect(page.getByRole('button', { name: 'Process Audiogram' })).toBeVisible();
  });

  test('17: Process button is disabled without file', async ({ page }) => {
    await page.goto(`${BASE_URL}/upload`);

    // Process button should be disabled
    const processButton = page.getByRole('button', { name: 'Process Audiogram' });
    await expect(processButton).toBeDisabled();
  });

  // =================================================================
  // Test 7: Delete Modal
  // =================================================================
  test('18: Delete modal appears when clicking delete', async ({ page }) => {
    await page.goto(`${BASE_URL}/tests/${TEST_ID}`);

    // Wait for data to load
    await page.waitForTimeout(1000);

    // Click Delete Test button
    await page.getByRole('button', { name: 'Delete Test' }).click();

    // Wait for modal
    await page.waitForTimeout(500);

    // Verify modal appears
    await expect(page.getByRole('heading', { name: 'Delete Test' })).toBeVisible();
    await expect(page.getByText(/Are you sure/)).toBeVisible();

    // Verify modal buttons - use last() to get the modal button, not the page button
    const cancelButtons = page.getByRole('button', { name: 'Cancel' });
    const deleteButtons = page.getByRole('button', { name: 'Delete', exact: true });

    await expect(cancelButtons.last()).toBeVisible();
    await expect(deleteButtons.last()).toBeVisible();

    // Click Cancel to close modal
    await cancelButtons.last().click();
  });

  // =================================================================
  // Test 8: Edit Test Data Button
  // =================================================================
  test('19: Edit Test Data button navigates to review page', async ({ page }) => {
    await page.goto(`${BASE_URL}/tests/${TEST_ID}`);

    // Wait for data to load
    await page.waitForTimeout(1000);

    // Click Edit Test Data button
    await page.getByRole('button', { name: 'Edit Test Data' }).click();

    // Should navigate to review page
    await expect(page).toHaveURL(`${BASE_URL}/tests/${TEST_ID}/review`);
  });

  // =================================================================
  // Test 9: Redirect from Root
  // =================================================================
  test('20: Root path redirects to dashboard', async ({ page }) => {
    await page.goto(BASE_URL);

    // Should redirect to dashboard
    await expect(page).toHaveURL(`${BASE_URL}/dashboard`);
  });

});
