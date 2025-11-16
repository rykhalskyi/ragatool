import { test, expect } from '@playwright/test';

test.describe('CollectionsListComponent', () => {
  test.beforeEach(async ({ page }) => {
    // Mock the API call to get collections
    await page.route('**/api/v1/collections/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { name: 'test-collection-1', id: '1', description: 'Description 1' },
          { name: 'test-collection-2', id: '2', description: 'Description 2' },
        ]),
      });
    });

    await page.goto('/');
  });

  test('should display collections', async ({ page }) => {
    await expect(page.getByText('test-collection-1')).toBeVisible();
    await expect(page.getByText('test-collection-2')).toBeVisible();
  });

  test('should navigate to collection details on click', async ({ page }) => {
    await page.getByText('test-collection-1').click();
    await expect(page).toHaveURL('/collection/1');
  });

  test('should open and close add collection dialog', async ({ page }) => {
    await page.getByRole('button', { name: 'Add Collection' }).click();
    await expect(page.getByRole('heading', { name: 'Add New Collection' })).toBeVisible();
    await page.getByRole('button', { name: 'Cancel' }).click();
    await expect(page.getByRole('heading', { name: 'Add New Collection' })).not.toBeVisible();
  });

  test('should add a new collection', async ({ page }) => {
    await page.route('POST', '**/api/v1/collections/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ name: 'new-collection', id: '3', description: '' }),
      });
    });

    await page.getByRole('button', { name: 'Add Collection' }).click();
    await page.getByLabel('Collection Name').fill('new-collection');
    await page.getByRole('button', { name: 'OK' }).click();

    await expect(page.getByText('new-collection')).toBeVisible();
  });

  test('should disable OK button when collection name is empty', async ({ page }) => {
    await page.getByRole('button', { name: 'Add Collection' }).click();
    const okButton = page.getByRole('button', { name: 'OK' });
    await expect(okButton).toBeDisabled();
    await page.getByLabel('Collection Name').fill('some-name');
    await expect(okButton).toBeEnabled();
    await page.getByLabel('Collection Name').clear();
    await expect(okButton).toBeDisabled();
  });
});
