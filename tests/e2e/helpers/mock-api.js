import {
  emptyTests,
  sampleTests,
  sampleTestDetails,
  uploadSuccessResponse,
  uploadReviewResponse,
  uploadErrorResponse
} from '../fixtures/mock-api-data.js';

/**
 * Set up API mocking for tests
 * This allows tests to run without a backend server
 *
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {Object} options - Mocking options
 * @param {boolean} options.hasTests - Whether to return tests or empty array
 * @param {boolean} options.uploadSuccess - Whether upload should succeed
 * @param {number|null} options.testId - Specific test ID to return details for
 */
export async function setupApiMocks(page, options = {}) {
  const {
    hasTests = false,
    uploadSuccess = true,
    testId = null
  } = options;

  // Mock GET /api/tests - List all tests
  await page.route('**/api/tests', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(hasTests ? sampleTests : emptyTests)
      });
    } else {
      await route.continue();
    }
  });

  // Mock GET /api/tests/:id - Get specific test details
  await page.route('**/api/tests/*', async (route) => {
    const url = route.request().url();
    const match = url.match(/\/api\/tests\/(\d+)/);

    if (route.request().method() === 'GET' && match) {
      const id = parseInt(match[1]);
      const testData = { ...sampleTestDetails, id };

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(testData)
      });
    } else {
      await route.continue();
    }
  });

  // Mock POST /api/upload - Upload audiogram
  await page.route('**/api/upload', async (route) => {
    if (route.request().method() === 'POST') {
      const response = uploadSuccess ? uploadSuccessResponse : uploadReviewResponse;

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(response)
      });
    } else {
      await route.continue();
    }
  });

  console.log(`🔧 API mocking enabled (hasTests: ${hasTests}, uploadSuccess: ${uploadSuccess})`);
}

/**
 * Set up API mocking with empty state (no tests)
 */
export async function setupEmptyStateMocks(page) {
  await setupApiMocks(page, { hasTests: false });
}

/**
 * Set up API mocking with test data
 */
export async function setupWithTestsMocks(page) {
  await setupApiMocks(page, { hasTests: true });
}

/**
 * Disable all API mocking
 */
export async function disableApiMocks(page) {
  await page.unroute('**/api/**');
  console.log('🔧 API mocking disabled');
}
