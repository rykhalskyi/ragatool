import { test, expect } from '@playwright/test';

test.describe('SelectedCollectionComponent', () => {
  test.beforeEach(async ({ page }) => {
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
                { name: 'test-collection', id: '123', description: 'A test collection', enabled: false, import_type: 'NONE' }
            ),
        });
    });

    await page.goto('/');
    await page.getByText('test-collection').click();
  });

  test('should display collection details', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'test-collection' })).toBeVisible();
    await expect(page.getByText('A test collection')).toBeVisible();
    await expect(page.getByRole('checkbox', { name: 'Enabled' })).not.toBeChecked();
  });

  test('should toggle collection enabled status', async ({ page }) => {
    await page.route('PUT', '**/api/v1/collections/123', async route => {
        const request = route.request();
        const postData = request.postDataJSON();
        expect(postData.enabled).toBe(true);
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(
                { name: 'test-collection', id: '123', description: 'A test collection', enabled: true, import_type: 'NONE' }
            ),
        });
    });

    await page.getByRole('checkbox', { name: 'Enabled' }).click();
    await expect(page.getByRole('checkbox', { name: 'Enabled' })).toBeChecked();
  });

  test('should edit and save description', async ({ page }) => {
    await page.route('PUT', '**/api/v1/collections/123', async route => {
        const request = route.request();
        const postData = request.postDataJSON();
        expect(postData.description).toBe('New description');
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(
                { name: 'test-collection', id: '123', description: 'New description', enabled: false, import_type: 'NONE' }
            ),
        });
    });

    await page.getByRole('button', { name: 'edit' }).click();
    await page.getByRole('textbox').fill('New description');
    await page.getByRole('button', { name: 'Save' }).click();
    await expect(page.getByText('New description')).toBeVisible();
  });

  test('should delete collection', async ({ page }) => {
    await page.route('DELETE', '**/api/v1/collections/123', async route => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ message: 'Collection deleted' }),
        });
    });

    page.on('dialog', async dialog => {
        expect(dialog.message()).toContain('Are you sure you want to delete the collection "test-collection"?');
        await dialog.accept();
    });

    await page.getByRole('button', { name: 'delete' }).click();
    await expect(page).toHaveURL('/');
  });
});
