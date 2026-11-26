import { expect, test, type Page } from '@playwright/test';
import { TestIds } from '../src/app/testing/test-ids';
import {
  ensureLoggedIn,
  TEST_PASSWORD,
  TEST_USERNAME,
} from './auth';

test.beforeEach(async ({ page }) => {
  await ensureLoggedIn(page);
});

async function openAccessTab(page: Page): Promise<void> {
  await page.getByTestId(TestIds.settingsButton).click();
  await expect(page).toHaveURL(/\/settings/);
  await page.getByTestId(TestIds.settingsTabAccess).click();
}

test('creates and revokes an API token', async ({ page }) => {
  await openAccessTab(page);

  await page.getByTestId(TestIds.createTokenButton).click();
  await page.getByTestId(TestIds.tokenNameInput).fill('playwright');
  await page.getByTestId(TestIds.tokenCreateSubmitButton).click();

  await expect(page.getByTestId(TestIds.tokenRevealValue)).toContainText('ragt_');
  await page.getByRole('button', { name: 'Done' }).click();

  const row = page.getByRole('row', { name: /playwright/ });
  await expect(row).toBeVisible();
  await row.getByTestId(TestIds.revokeTokenButton).click();
  await page.getByTestId(TestIds.deleteConfirmButton).click();

  await expect(row).toContainText('Revoked');
});

test('logs out and back in', async ({ page }) => {
  await openAccessTab(page);
  await page.getByTestId(TestIds.logoutButton).click();
  await expect(page).toHaveURL(/\/login$/);

  await page.getByTestId(TestIds.loginUsernameInput).fill(TEST_USERNAME);
  await page.getByTestId(TestIds.loginPasswordInput).fill(TEST_PASSWORD);
  await page.getByTestId(TestIds.loginSubmitButton).click();

  await expect(page).not.toHaveURL(/\/login$/);
});
