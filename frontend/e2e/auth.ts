import { Page } from '@playwright/test';
import { TestIds } from '../src/app/testing/test-ids';

export const TEST_USERNAME = 'admin';
export const TEST_PASSWORD = 'password123';

/**
 * Ensure the browser has a session before a scenario runs.
 *
 * CI seeds the admin with RAGATOOL_ADMIN_PASSWORD_HASH so the first-run
 * setup screen does not appear. Locally, create the account once through the
 * UI or run the backend with the same environment variable.
 */
export async function ensureLoggedIn(page: Page): Promise<void> {
  await page.goto('/');
  await page.waitForTimeout(500);

  if (page.url().includes('/setup')) {
    throw new Error(
      'Backend is not seeded for tests. Start it with ' +
        'RAGATOOL_ADMIN_PASSWORD_HASH set to the hash of "password123".'
    );
  }

  if (!page.url().includes('/login')) {
    return;
  }

  await page.getByTestId(TestIds.loginUsernameInput).fill(TEST_USERNAME);
  await page.getByTestId(TestIds.loginPasswordInput).fill(TEST_PASSWORD);
  await page.getByTestId(TestIds.loginSubmitButton).click();
  await page.waitForURL((url) => !url.pathname.startsWith('/login'));
}
