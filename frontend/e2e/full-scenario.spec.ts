import { test, expect } from '@playwright/test';
import * as path from 'path';

const draculaFilePath = path.resolve(__dirname, 'text/dracula.txt');
const lotrFilePath = path.resolve(__dirname, 'text/The Lord of the Rings.txt');

test.describe('Full E2E Scenario', () => {
  test.beforeAll(async ({ browser }) => {
    const page = await browser.newPage();
    await page.goto('http://localhost:4200');

    // Delete Dracula if it exists
    const draculaRow = page.locator('tr', { hasText: 'Dracula' });
    if (await draculaRow.isVisible()) {
      await draculaRow.getByRole('button', { name: 'Delete' }).click();
      await page.getByRole('button', { name: 'Yes, delete' }).click();
      await expect(page.getByText('Dracula')).not.toBeVisible();
    }

    // Delete The Lord of the Rings if it exists
    const lotrRow = page.locator('tr', { hasText: 'The Lord of the Rings' });
    if (await lotrRow.isVisible()) {
        await lotrRow.getByRole('button', { name: 'Delete' }).click();
        await page.getByRole('button', { name: 'Yes, delete' }).click();
        await expect(page.getByText('The Lord of the Rings')).not.toBeVisible();
    }
    await page.close();
  });

  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:4200');
  });

  test('should perform a full end-to-end scenario', async ({ page }) => {
    await test.step('Add "Dracula" collection', async () => {
      await page.getByRole('button', { name: 'Add Collection' }).click();
      await page.getByLabel('Collection Name').fill('Dracula');
      await page.getByRole('button', { name: 'OK' }).click();
      await expect(page.getByText('Dracula')).toBeVisible();
    });

    await test.step('Add "The Lord of the Rings" collection', async () => {
      await page.getByRole('button', { name: 'Add Collection' }).click();
      await page.getByLabel('Collection Name').fill('The Lord of the Rings');
  //    await page.getByLabel('Description').fill('A book about a hobbit and a ring.');
      await page.getByRole('button', { name: 'OK' }).click();
      await expect(page.getByText('The Lord of the Rings')).toBeVisible();
    });

    await test.step('should change "Dracula "collection description', async () => {
      await page.getByText('Dracula').click();
      await page.getByRole('button').filter({ hasText: 'edit' }).click();
      await page.getByRole('textbox').fill('A book about a vampire.');
      await page.getByRole('button', { name: 'Save' }).click();
      await expect(page.getByText('A book about a vampire.')).toBeVisible();
    });

    await test.step('should change "The Lord of the Rings "collection description', async () => {
      await page.getByText('The Lord of the Rings').click();
      await page.getByRole('button').filter({ hasText: 'edit' }).click();
      await page.getByRole('textbox').fill('A book about a hobbit and a ring..');
      await page.getByRole('button', { name: 'Save' }).click();
      await expect(page.getByText('A book about a hobbit and a ring.')).toBeVisible();
    });

    await test.step('Import file to "Dracula" collection', async () => {
      await page.getByText('Dracula').click();
      await expect(page).toHaveURL(/\/collection\/.*/);

      await page.getByTestId('import-button').click();
      await page.getByRole('button', { name: 'Pick File' }).click();

      // Close the dropdown by pressing Escape
     // await page.keyboard.press('Escape');

      
      // Assert that the import dialog is shown
      await expect(page.getByRole('heading', { name: /Import File to .*/ })).toBeVisible();

      const fileChooserPromise = page.waitForEvent('filechooser');
      const fileChooser = await fileChooserPromise;
      await fileChooser.setFiles(draculaFilePath);

      await page.getByRole('button', { name: 'Pick File' }).click();

      await expect(page.getByText('Import completed')).toBeVisible({ timeout: 60000 });
      await page.getByRole('button', { name: 'Close' }).click();
    });

    await test.step('Navigate back and import file to "The Lord of the Rings" collection', async () => {
      // Navigate back to the collections list. 
      // Using goBack() is more resilient than clicking a link.
      await page.goBack();
      await expect(page).toHaveURL('http://localhost:4200/');
      
      await page.getByText('The Lord of the Rings').click();
      await expect(page).toHaveURL(/\/collection\/.*/);

      await page.getByTestId('import-select').click();
      await page.getByRole('option', { name: 'FILE' }).click();
      
      // Close the dropdown by pressing Escape
      await page.keyboard.press('Escape');
      
      // Click the Import File button to open the dialog
      await page.getByRole('button', { name: 'Import File' }).click();

      // Assert that the import dialog is shown
      await expect(page.getByRole('heading', { name: /Import File to .*/ })).toBeVisible();
      
      const fileChooserPromise = page.waitForEvent('filechooser');
      const fileChooser = await fileChooserPromise;
      await fileChooser.setFiles(lotrFilePath);
      await page.getByRole('button', { name: 'Import' }).click();

      await expect(page.getByText('Import completed')).toBeVisible({ timeout: 120000 });
      await page.getByRole('button', { name: 'Close' }).click();
    });

    await test.step('Enable and disable "Dracula" on MCP', async () => {
        const draculaRow = page.locator('tr', { hasText: 'Dracula' });
        
        // Enable
        await draculaRow.getByLabel('Enable on MCP').click();
        await expect(draculaRow.getByLabel('Disable on MCP')).toBeVisible();

        // Disable
        await draculaRow.getByLabel('Disable on MCP').click();
        await expect(draculaRow.getByLabel('Enable on MCP')).toBeVisible();
    });

    await test.step('Enable "The Lord of the Rings" on MCP', async () => {
        const lotrRow = page.locator('tr', { hasText: 'The Lord of the Rings' });
        await lotrRow.getByLabel('Enable on MCP').click();
        await expect(lotrRow.getByLabel('Disable on MCP')).toBeVisible();
    });

    await test.step('Search in "Dracula" collection', async () => {
      await page.getByText('Dracula').click();
      await page.getByPlaceholder('Search...').fill('castle');
      await page.getByRole('button', { name: 'Search' }).click();

      const results = page.locator('mat-list-item');
      await expect(results).toHaveCount(5);
      await expect(results.first()).toContainText('castle');
    });
  });

  test.afterEach(async ({ page }) => {
    // Go to collections page
    await page.goto('http://localhost:4200');

    // Delete Dracula if it exists
    const draculaRow = page.locator('tr', { hasText: 'Dracula' });
    if (await draculaRow.isVisible()) {
      await draculaRow.getByRole('button', { name: 'Delete' }).click();
      await page.getByRole('button', { name: 'Yes, delete' }).click();
      await expect(page.getByText('Dracula')).not.toBeVisible();
    }

    // Delete The Lord of the Rings if it exists
    const lotrRow = page.locator('tr', { hasText: 'The Lord of the Rings' });
    if (await lotrRow.isVisible()) {
        await lotrRow.getByRole('button', { name: 'Delete' }).click();
        await page.getByRole('button', { name: 'Yes, delete' }).click();
        await expect(page.getByText('The Lord of the Rings')).not.toBeVisible();
    }
  });
});
