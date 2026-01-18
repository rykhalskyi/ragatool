import { test, expect } from '@playwright/test';

test.describe('Inspect Dialog E2E Tests', () => {

  test('should open Inspect Dialog from collection details and navigate chunks', async ({ page }) => {
    // Navigate to a collection details page (assuming a collection exists)
    // For this E2E test, we'll assume a collection with ID 'test-collection' exists
    // and the route to its details page is something like '/collections/test-collection'
    // This part might need adjustment based on actual routing and data setup
    await page.goto('/collections'); // Or the specific collection route if available

    // Simulate clicking on a collection to get to its details
    // This assumes there's at least one collection listed
    await page.waitForSelector('mat-card-title');
    await page.click('mat-card-title'); // Click on the first collection listed

    // Wait for the details to load and the Inspect button to be visible
    await page.waitForSelector('button:has-text("Inspect")');
    await page.click('button:has-text("Inspect")');

    // Verify the Inspect Dialog is open
    await expect(page.locator('h1.mat-mdc-dialog-title:has-text("Inspect Collection")')).toBeVisible();

    // Verify Inspect tab is active
    await expect(page.locator('mat-tab-group .mat-tab-label-active:has-text("Inspect")')).toBeVisible();

    // Expect initial chunk to be loaded
    await expect(page.locator('.chunk-viewer p')).not.toBeEmpty();

    // Click Next and verify chunk changes
    await page.click('button:has-text("Next")');
    // We can't assert specific content without knowing the test data,
    // but we can assert it's not empty and the current chunk index has conceptually moved
    await expect(page.locator('.chunk-viewer p')).not.toBeEmpty();

    // Click Previous and verify chunk changes
    await page.click('button:has-text("Previous")');
    await expect(page.locator('.chunk-viewer p')).not.toBeEmpty();
  });

  test('should switch to Query tab and submit a query', async ({ page }) => {
    await page.goto('/collections');
    await page.waitForSelector('mat-card-title');
    await page.click('mat-card-title');

    await page.waitForSelector('button:has-text("Inspect")');
    await page.click('button:has-text("Inspect")');

    await expect(page.locator('h1.mat-mdc-dialog-title:has-text("Inspect Collection")')).toBeVisible();

    // Switch to Query tab
    await page.click('mat-tab-group button:has-text("Query")');
    await expect(page.locator('mat-tab-group .mat-tab-label-active:has-text("Query")')).toBeVisible();

    // Type a query
    const queryInput = page.locator('mat-form-field.query-input-field input');
    await expect(queryInput).toBeVisible();
    await queryInput.fill('What is RAG?');

    // Submit query
    await page.click('button:has-text("Send")');

    // Expect user message to appear
    await expect(page.locator('.chat-message.user-message:has-text("What is RAG?")')).toBeVisible();

    // Expect bot response to appear (this might need to be more robust depending on actual API response)
    await expect(page.locator('.chat-message.bot-message')).toBeVisible();
    await expect(page.locator('.chat-message.bot-message p')).not.toBeEmpty();
  });

  test('should close the Inspect Dialog', async ({ page }) => {
    await page.goto('/collections');
    await page.waitForSelector('mat-card-title');
    await page.click('mat-card-title');

    await page.waitForSelector('button:has-text("Inspect")');
    await page.click('button:has-text("Inspect")');

    await expect(page.locator('h1.mat-mdc-dialog-title:has-text("Inspect Collection")')).toBeVisible();

    // Close the dialog
    await page.click('mat-dialog-actions button:has-text("Close")');

    // Verify dialog is closed
    await expect(page.locator('h1.mat-mdc-dialog-title:has-text("Inspect Collection")')).not.toBeVisible();
  });
});
