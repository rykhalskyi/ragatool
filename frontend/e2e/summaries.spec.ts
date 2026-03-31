import { test, expect } from '@playwright/test';
import { TestIds } from '../src/app/testing/test-ids';
import path from 'path';

test('Summaries UI Scenario', async ({ page }) => {
  const filePath = path.resolve(__dirname, 'text/dracula.txt');

  await test.step('Setup: Add a collection with some content', async () => {
    await page.goto('/');
    
    // Delete Dracula_Summary if exists
    const collectionItem = page.getByTestId(`${TestIds.collectionItem}-Dracula_Summary`);
    if (await collectionItem.isVisible()) {
      await collectionItem.click();
      await page.getByTestId(TestIds.deleteCollectionButton).click();
      await page.getByTestId(TestIds.deleteConfirmButton).click();
    }

    // Add Collection
    await page.getByTestId(TestIds.addCollectionButton).click();
    await page.getByTestId(TestIds.addCollectionNameInput).fill('Dracula_Summary');
    await page.getByTestId(TestIds.addCollectionOkButton).click();
    
    await page.getByTestId(`${TestIds.collectionItem}-Dracula_Summary`).click();

    // Import some data (one-step import)
    // Make sure two-step is OFF
    await page.getByTestId(TestIds.settingsButton).click();
    const twoStepSwitch = page.getByTestId(TestIds.twoStepImportSwitch);
    const switchButton = twoStepSwitch.getByRole('switch');
    if (await switchButton.isChecked()) {
      await switchButton.click();
    }
    await page.getByTestId(TestIds.saveSettingsButton).click();

    await page.getByTestId(`${TestIds.collectionItem}-Dracula_Summary`).click();
    await page.getByTestId(TestIds.importTypeSelect).click();
    await page.getByRole('option', { name: 'File' }).click();
    
    await page.locator('input[type="file"]').setInputFiles(filePath);
    await page.getByTestId(TestIds.importButton).click();

    await expect(page.getByTestId(TestIds.chunkCountText)).toBeVisible({ timeout: 10000 });
  });

  await test.step('1. Open Summary Dialog', async () => {
    await page.getByTestId(TestIds.summaryButton).click();
    await expect(page.getByTestId(TestIds.summaryDialogTitle)).toBeVisible();
    await expect(page.getByText('No summaries found.')).toBeVisible();
  });

  await test.step('2. Add a new summary', async () => {
    await page.getByTestId(TestIds.addSummaryButton).click();
    
    // Fill form
    await page.locator('input[placeholder="Summary title"]').fill('Chapter 1 Summary');
    await page.locator('textarea[placeholder="Summary content"]').fill('This is a test summary for Chapter 1.');
    
    await page.getByTestId(TestIds.saveSummaryButton).click();

    // Verify it appeared in the list
    await expect(page.getByTestId(TestIds.summaryListItem).filter({ hasText: 'Chapter 1 Summary' })).toBeVisible();
    await expect(page.getByTestId(TestIds.summaryLevelLabel)).toContainText('CHUNK');
    await expect(page.getByTestId(TestIds.summaryContentPreview)).toContainText('This is a test summary for Chapter 1.');
  });

  await test.step('3. Edit the summary', async () => {
    await page.getByTestId(TestIds.editSummaryButton).click();
    
    await page.locator('textarea[placeholder="Summary content"]').fill('Updated summary content.');
    await page.getByTestId(TestIds.saveSummaryButton).click();

    await expect(page.getByTestId(TestIds.summaryContentPreview)).toContainText('Updated summary content.');
  });

  await test.step('4. Delete the summary', async () => {
    // We need to handle the confirmation dialog if it uses window.confirm
    page.on('dialog', dialog => dialog.accept());
    
    await page.getByTestId(TestIds.deleteSummaryButton).click();

    await expect(page.getByText('No summaries found.')).toBeVisible();
  });

  await test.step('Cleanup', async () => {
    await page.getByRole('button', { name: 'Close' }).click();
    await page.getByTestId(TestIds.deleteCollectionButton).click();
    await page.getByTestId(TestIds.deleteConfirmButton).click();
  });
});
