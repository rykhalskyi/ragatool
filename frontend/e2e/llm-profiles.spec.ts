import { test, expect } from '@playwright/test';
import { ensureLoggedIn } from './auth';
import { TestIds } from '../src/app/testing/test-ids';

const providers = [
  {
    id: 'openai',
    label: 'OpenAI',
    default_base_url: 'https://api.openai.com/v1',
    default_model: 'gpt-4o-mini',
    requires_api_key: true,
  },
  {
    id: 'deepseek',
    label: 'DeepSeek',
    default_base_url: 'https://api.deepseek.com',
    default_model: 'deepseek-chat',
    requires_api_key: true,
  },
];

test.describe('LLM API profiles', () => {
  test('adds a profile from Settings', async ({ page }) => {
    let profiles: Record<string, unknown>[] = [];

    await page.route('**/agent/providers', (route) =>
      route.fulfill({ json: providers })
    );
    await page.route('**/agent/profiles', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({ json: profiles });
        return;
      }
      if (route.request().method() === 'POST') {
        const body = route.request().postDataJSON() as Record<string, unknown>;
        const created = {
          ...body,
          id: 'profile-1',
          api_key_masked: '••••••••1234',
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: null,
        };
        profiles = [created];
        await route.fulfill({ status: 201, json: created });
        return;
      }
      await route.continue();
    });

    await ensureLoggedIn(page);
    await page.goto('/settings');

    await expect(page.getByTestId(TestIds.llmProfilesSection)).toBeVisible();
    await expect(page.getByTestId(TestIds.llmProfilesEmpty)).toBeVisible();

    await page.getByTestId(TestIds.addLlmProfileButton).click();
    await page.getByTestId(TestIds.llmProfileNameInput).fill('Test profile');
    await page.getByTestId(TestIds.llmProfileApiKeyInput).fill('sk-test-1234');
    await page.getByTestId(TestIds.llmProfileSaveButton).click();

    const card = page.getByTestId(TestIds.llmProfileCard);
    await expect(card).toHaveCount(1);
    await expect(card).toContainText('Test profile');
    await expect(card).toContainText('••••••••1234');
    await expect(card).toContainText('Active');
  });
});
