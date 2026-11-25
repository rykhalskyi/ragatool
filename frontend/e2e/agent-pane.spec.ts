import { Page, expect, test } from '@playwright/test';
import { TestIds } from '../src/app/testing/test-ids';
import { ensureLoggedIn } from './auth';

const profile = {
  id: 'profile-1',
  name: 'Mock profile',
  provider: 'openai',
  base_url: 'https://example.invalid/v1',
  model: 'mock-model',
  temperature: 0.2,
  max_tokens: 512,
  connect_timeout_seconds: 5,
  read_timeout_seconds: 5,
  api_key_masked: '••••••••1234',
  is_active: true,
  created_at: new Date().toISOString(),
  updated_at: null,
};

async function mockAgentApi(page: Page, profiles = [profile]) {
  const requests: Record<string, unknown>[] = [];

  await page.route('**/agent/profiles', (route) => route.fulfill({ json: profiles }));
  await page.route('**/agent/chat', async (route) => {
    const body = route.request().postDataJSON() as Record<string, unknown>;
    requests.push(body);
    const wantsTool = String(body['message']).includes('tool');
    await route.fulfill({
      json: {
        message: wantsTool ? 'I found supporting passages.' : 'A concise answer.',
        model: 'mock-model',
        tool_calls: wantsTool
          ? [
              {
                id: 'call-1',
                name: 'query_collection',
                arguments: { collection_name: 'books', query_text: 'dune' },
                status: 'success',
                result_preview: '{"status": "success", "results": []}',
              },
            ]
          : [],
        usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 },
        warnings: [],
      },
    });
  });

  return requests;
}

async function openAgentPane(page: Page) {
  await page.getByTestId(TestIds.agentToggleButton).click();
  await expect(page.getByTestId(TestIds.agentPane)).toBeVisible();
}

test.beforeEach(async ({ page }) => {
  await ensureLoggedIn(page);
});

test('opens the pane, sends a message, and shows tool calls', async ({ page }) => {
  const requests = await mockAgentApi(page);

  await page.goto('/collection');
  await openAgentPane(page);

  await expect(page.getByTestId(TestIds.agentProfileChip)).toContainText('Mock profile');
  await expect(page.getByTestId(TestIds.agentEmptyState)).toBeVisible();

  await page.getByTestId(TestIds.agentComposer).fill('What is this collection?');
  await page.getByTestId(TestIds.agentComposer).press('Enter');

  await expect(page.getByTestId(TestIds.agentUserMessage)).toContainText(
    'What is this collection?'
  );
  await expect(page.getByTestId(TestIds.agentAssistantMessage)).toContainText(
    'A concise answer.'
  );

  await page.getByTestId(TestIds.agentComposer).fill('Use a tool please');
  await page.getByTestId(TestIds.agentSendButton).click();

  await expect(page.getByTestId(TestIds.agentToolCall)).toBeVisible();
  await expect(page.getByTestId(TestIds.agentToolCall)).toContainText('query_collection');
  expect(requests).toHaveLength(2);
});

test('keeps history across chats, reloads, and hide/show', async ({ page }) => {
  await mockAgentApi(page);

  await page.goto('/collection');
  await openAgentPane(page);
  await page.getByTestId(TestIds.agentComposer).fill('Remember this message');
  await page.getByTestId(TestIds.agentSendButton).click();
  await expect(page.getByTestId(TestIds.agentAssistantMessage)).toBeVisible();

  await page.getByTestId(TestIds.agentNewChatButton).click();
  await expect(page.getByTestId(TestIds.agentEmptyState)).toBeVisible();

  await expect(page.getByTestId(TestIds.agentChatSelect).locator('option')).toHaveCount(2);
  const firstChatValue = await page
    .getByTestId(TestIds.agentChatSelect)
    .locator('option')
    .first()
    .getAttribute('value');
  await page.getByTestId(TestIds.agentChatSelect).selectOption(firstChatValue as string);
  await expect(page.getByTestId(TestIds.agentUserMessage)).toContainText(
    'Remember this message'
  );

  await page.getByTestId(TestIds.agentCloseButton).click();
  await expect(page.getByTestId(TestIds.agentPane)).not.toBeVisible();
  await openAgentPane(page);
  await expect(page.getByTestId(TestIds.agentUserMessage)).toContainText(
    'Remember this message'
  );

  await page.reload();
  await expect(page.getByTestId(TestIds.agentPane)).toBeVisible();
  await expect(page.getByTestId(TestIds.agentUserMessage)).toContainText(
    'Remember this message'
  );
});

test('resizes the pane and persists the width', async ({ page }) => {
  await mockAgentApi(page);

  await page.goto('/collection');
  await openAgentPane(page);

  const handle = page.getByTestId(TestIds.agentResizeHandle);
  const box = await handle.boundingBox();
  expect(box).not.toBeNull();

  const before = await page.evaluate(() => {
    const raw = localStorage.getItem('ragatool.agent.pane.v1');
    return raw ? (JSON.parse(raw) as { width: number }).width : 0;
  });

  await page.mouse.move(box!.x + box!.width / 2, box!.y + 100);
  await page.mouse.down();
  await page.mouse.move(box!.x - 120, box!.y + 100, { steps: 5 });
  await page.mouse.up();

  const after = await page.evaluate(() => {
    const raw = localStorage.getItem('ragatool.agent.pane.v1');
    return raw ? (JSON.parse(raw) as { width: number }).width : 0;
  });
  expect(after).toBeGreaterThan(before);

  await page.reload();
  await expect(page.getByTestId(TestIds.agentPane)).toBeVisible();
  const persisted = await page.evaluate(() => {
    const raw = localStorage.getItem('ragatool.agent.pane.v1');
    return raw ? (JSON.parse(raw) as { width: number }).width : 0;
  });
  expect(persisted).toBe(after);
});

test('shows the no-profile state and links to Settings', async ({ page }) => {
  await mockAgentApi(page, []);

  await page.goto('/collection');
  await openAgentPane(page);

  await expect(page.getByTestId(TestIds.agentNoProfile)).toBeVisible();
  await page.getByTestId(TestIds.agentSettingsLink).click();
  await expect(page).toHaveURL(/\/settings\?tab=agent-api$/);
});

test('shows the selected collection as context', async ({ page }) => {
  const requests = await mockAgentApi(page);
  const collection = {
    id: 'col-1',
    name: 'Books',
    description: 'Book collection',
    enabled: true,
    import_type: 'NONE',
    model: null,
    settings: null,
  };

  await page.route('**/collections**', async (route) => {
    const url = route.request().url();
    if (url.includes('/details')) {
      await route.fulfill({ json: { ...collection, metadata: {}, count: 1 } });
    } else if (/\/collections\/col-1$/.test(url)) {
      await route.fulfill({ json: collection });
    } else {
      await route.fulfill({ json: [collection] });
    }
  });
  await page.route('**/files/col-1', (route) => route.fulfill({ json: [] }));

  await page.goto('/collection/col-1');
  await openAgentPane(page);

  await expect(page.getByTestId(TestIds.agentCollectionChip)).toContainText('Books');

  await page.getByTestId(TestIds.agentComposer).fill('Summarize this');
  await page.getByTestId(TestIds.agentSendButton).click();

  expect(requests[0]['collection_name']).toBe('Books');
});
