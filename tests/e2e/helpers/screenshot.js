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
