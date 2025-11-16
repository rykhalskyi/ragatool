import { test, expect } from '@playwright/test';

test.describe('TopbarComponent', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display the title', async ({ page }) => {
    await expect(page.getByText('Ragatouille')).toBeVisible();
  });

  test('should display the logo', async ({ page }) => {
    await expect(page.getByRole('img', { name: 'Ragatouille Logo' })).toBeVisible();
  });
});
