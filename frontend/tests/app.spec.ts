import { test, expect } from '@playwright/test';

test('has title', async ({ page }) => {
  await page.goto('/');

  // Expect a title "to contain" a substring.
  await expect(page).toHaveTitle(/Ragatouille/);
});

test('has topbar', async ({ page }) => {
  await page.goto('/');

  // Expect topbar to be visible
  await expect(page.locator('app-topbar')).toBeVisible();
});

test('has collections list', async ({ page }) => {
    await page.goto('/');
  
    // Expect collections-list to be visible
    await expect(page.locator('app-collections-list')).toBeVisible();
});
