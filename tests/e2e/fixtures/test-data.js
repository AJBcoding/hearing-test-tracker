/**
 * Test data for E2E tests
 * These values are used across different test scenarios
 */

/**
 * Path to test audiogram image file
 * This should be a sample audiogram image for testing uploads
 */
export const testAudiogramPath = 'tests/e2e/fixtures/sample-audiogram.jpg';

/**
 * Wait times for common scenarios (in milliseconds)
 */
export const waitTimes = {
  shortDelay: 500,
  navigation: 1000,
  apiResponse: 2000,
  uploadProcessing: 5000,  // OCR/processing may take longer
};

/**
 * Selectors for common elements
 */
export const selectors = {
  // Navigation
  navDashboard: 'a[href="/dashboard"]',
  navUpload: 'a[href="/upload"]',
  navTests: 'a[href="/tests"]',
  appTitle: 'text=Hearing Test Tracker',

  // Dashboard
  dashboardTitle: 'text=No tests yet',  // Empty state
  uploadTestButton: 'button:has-text("Upload Test")',
  totalTestsCard: 'text=Total Tests',
  latestTestCard: 'text=Latest Test',
  testsThisYearCard: 'text=Tests This Year',
  viewDetailsButton: 'button:has-text("View Details")',
  viewAllButton: 'button:has-text("View All")',
  recentTestsTable: 'table',

  // Upload page
  uploadPageTitle: 'h1:has-text("Upload Hearing Test")',
  singleUploadTab: 'button[role="tab"]:has-text("Single Upload")',
  bulkUploadTab: 'button[role="tab"]:has-text("Bulk Upload")',
  fileInput: 'input[type="file"]',
  processButton: 'button:has-text("Process Audiogram")',
  uploadError: '[role="alert"]:has-text("Upload Failed")',

  // Test list page
  testListTable: 'table',
  testRow: 'table tbody tr',
  viewTestButton: 'button:has-text("View")',

  // Test viewer page
  testDetailsCard: 'text=Test Details',
  audiogramChart: 'text=Audiogram',  // Look for chart/visualization
  confidenceBadge: '[class*="Badge"]',

  // Test review/edit page
  reviewTitle: 'text=Review',
  saveButton: 'button:has-text("Save")',
  cancelButton: 'button:has-text("Cancel")',

  // Common
  loadingText: 'text=Loading...',
  notification: '[class*="Notification"]',
};

/**
 * Expected values for assertions
 */
export const expectedValues = {
  appTitle: 'Hearing Test Tracker',
  emptyStateMessage: 'No tests yet',
  uploadSuccessMessage: 'Upload Successful',
  minConfidenceForAutoAccept: 0.8,  // 80% confidence
};

/**
 * Routes
 */
export const routes = {
  home: '/',
  dashboard: '/dashboard',
  upload: '/upload',
  tests: '/tests',
  testViewer: (id) => `/tests/${id}`,
  testReview: (id) => `/tests/${id}/review`,
};
