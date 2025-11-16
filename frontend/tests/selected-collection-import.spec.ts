import { test, expect } from '@playwright/test';

test.describe('SelectedCollectionImportComponent', () => {
  test.beforeEach(async ({ page }) => {
    // Mock the API call to get import types
    await page.route('**/api/v1/import/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { name: 'PDF', embedding_model: 'model1', chunk_size: 100, chunk_overlap: 10 },
          { name: 'TXT', embedding_model: 'model2', chunk_size: 200, chunk_overlap: 20 },
          { name: 'FILE', embedding_model: 'model3', chunk_size: 300, chunk_overlap: 30 },
        ]),
      });
    });

    // Mock the API call to get collections
    await page.route('**/api/v1/collections/', async route => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify([
                { name: 'test-collection', id: '123', description: 'A test collection' },
            ]),
        });
    });

    // Mock the API call to get a single collection
    await page.route('**/api/v1/collections/123', async route => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(
                { name: 'test-collection', id: '123', description: 'A test collection' }
            ),
        });
    });

    await page.goto('/');
    await page.getByText('test-collection').click();
  });

  test('should render the form', async ({ page }) => {
    await expect(page.locator('app-selected-collection-import')).toBeVisible();
    await expect(page.getByLabel('Select Import Type')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Pick File' })).toBeVisible();
    await expect(page.getByLabel('Model')).toBeVisible();
    await expect(page.getByLabel('Chunk Size')).toBeVisible();
    await expect(page.getByLabel('Chunk Overlap')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Import' })).toBeVisible();
  });

  test('should load import types in the select', async ({ page }) => {
    await page.getByLabel('Select Import Type').click();
    await expect(page.getByText('PDF')).toBeVisible();
    await expect(page.getByText('TXT')).toBeVisible();
  });

  test('should enable the Import button when the form is valid', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Import' })).toBeDisabled();

    await page.getByLabel('Select Import Type').click();
    await page.getByText('FILE').click();

    await page.getByLabel('Model').fill('test-model');
    await page.getByLabel('Chunk Size').fill('100');
    await page.getByLabel('Chunk Overlap').fill('10');

    // Mock file upload
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.getByRole('button', { name: 'Pick File' }).click();
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles({
        name: 'test.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from('test'),
    });

    await expect(page.getByRole('button', { name: 'Import' })).toBeEnabled();
  });

  test('should show error for required importType when touched', async ({ page }) => {
    await page.getByLabel('Select Import Type').click();
    await page.getByLabel('Select Import Type').blur();
    await expect(page.getByText('Import type is required.')).toBeVisible();
  });

  test('should show error for required model when touched', async ({ page }) => {
    await page.getByLabel('Model').click();
    await page.getByLabel('Model').blur();
    await expect(page.getByText('Model is required.')).toBeVisible();
  });

  test('should show error for required chunk size when touched', async ({ page }) => {
    await page.getByLabel('Chunk Size').click();
    await page.getByLabel('Chunk Size').blur();
    await expect(page.getByText('Chunk size is required.')).toBeVisible();
  });

  test('should show error for min chunk size when invalid', async ({ page }) => {
    await page.getByLabel('Chunk Size').fill('0');
    await page.getByLabel('Chunk Size').blur();
    await expect(page.getByText('Chunk size must be at least 1.')).toBeVisible();
  });

  test('should show error for required chunk overlap when touched', async ({ page }) => {
    await page.getByLabel('Chunk Overlap').click();
    await page.getByLabel('Chunk Overlap').blur();
    await expect(page.getByText('Chunk overlap is required.')).toBeVisible();
  });

  test('should show error for min chunk overlap when invalid', async ({ page }) => {
    await page.getByLabel('Chunk Overlap').fill('-1');
    await page.getByLabel('Chunk Overlap').blur();
    await expect(page.getByText('Chunk overlap must be at least 0.')).toBeVisible();
  });

  test('should submit the form with valid data', async ({ page }) => {
    await page.getByLabel('Select Import Type').click();
    await page.getByText('FILE').click();

    await page.getByLabel('Model').fill('test-model');
    await page.getByLabel('Chunk Size').fill('100');
    await page.getByLabel('Chunk Overlap').fill('10');

    // Mock file upload
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.getByRole('button', { name: 'Pick File' }).click();
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles({
        name: 'test.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from('test'),
    });

    // Mock the import API call
    await page.route('**/api/v1/import/123', async route => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ message: 'Import successful' }),
        });
    });

    const requestPromise = page.waitForRequest('**/api/v1/import/123');
    await page.getByRole('button', { name: 'Import' }).click();
    const request = await requestPromise;

    const postData = request.postDataJSON();
    expect(postData).toBeDefined();
  });

  test('should disable importType and model fields when collection is saved', async ({ page }) => {
    // Mock the API call to get a single collection with import_type set
    await page.route('**/api/v1/collections/123', async route => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(
                { name: 'test-collection', id: '123', description: 'A test collection', import_type: 'FILE' }
            ),
        });
    });

    await page.goto('/');
    await page.getByText('test-collection').click();

    await expect(page.getByLabel('Select Import Type')).toBeDisabled();
    await expect(page.getByLabel('Model')).toBeDisabled();
  });
});
