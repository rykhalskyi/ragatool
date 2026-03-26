import { test, expect } from '@playwright/test';
import { TestIds } from '../src/app/testing/test-ids';
import path from 'path';

test('Dracula_2 Popups Scenario', async ({ page }) => {
  const filePath = path.resolve(__dirname, 'text/dracula.txt');

  await test.step('Once Before tests: delete Dracula_2 if exists', async () => {
    await page.goto('/');
    
    // Check if Dracula_2 exists and delete it
    const collectionItem = page.getByTestId(`${TestIds.collectionItem}-Dracula_2`);
    if (await collectionItem.isVisible()) {
      await collectionItem.click();
      await page.getByTestId(TestIds.deleteCollectionButton).click();
      await page.getByTestId(TestIds.deleteConfirmButton).click();
      await expect(collectionItem).not.toBeVisible();
    }
  });

  await test.step('1. Add Dracula_2 collection with two-step import and popups', async () => {
    // 1. Enable two-step import in settings
    await page.getByTestId(TestIds.settingsButton).click();
    const twoStepSwitch = page.getByTestId(TestIds.twoStepImportSwitch);
    const switchButton = twoStepSwitch.getByRole('switch');
    if (!(await switchButton.isChecked())) {
      await switchButton.click();
    }
    await expect(switchButton).toBeChecked();

    await page.getByTestId(TestIds.saveSettingsButton).click();

    // 2. Add Collection
    await page.getByTestId(TestIds.addCollectionButton).click();
    await expect(page.getByTestId(TestIds.addCollectionDialogTitle)).toBeVisible();
    await page.getByTestId(TestIds.addCollectionNameInput).fill('Dracula_2');
    await page.getByTestId(TestIds.addCollectionOkButton).click();
    
    const collectionItem = page.getByTestId(`${TestIds.collectionItem}-Dracula_2`);
    await expect(collectionItem).toBeVisible();

    await collectionItem.click();

    // 3. Step 1: Load File
    await page.getByTestId(TestIds.importTypeSelect).click();
    await page.getByRole('option', { name: 'File' }).click();              
    await page.getByTestId(TestIds.importStep1Button).click();

    // Pick File
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.getByTestId(TestIds.pickFileButton).click(); 
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(filePath);

    await page.getByTestId(TestIds.chunkSizeInput).fill('500');
    await page.getByTestId(TestIds.chunkOverlapInput).fill('50');
    await page.getByTestId(TestIds.importFileSubmitButton).click();

    // wait until element 'progress' hidden
    await expect(page.getByTestId(TestIds.importProgress)).not.toBeVisible({ timeout: 5000 });
    
    // 4. Step 2: Preview and Import
    await page.getByTestId(TestIds.importStep2Button).click({timeout: 2000});
    
    // Select the file in preview dialog
    await page.getByTestId(TestIds.previewDialogFileItem).filter({ hasText: 'dracula.txt' }).first().click();
    
    // Verify chunking parameters in preview
    await expect(page.getByTestId(TestIds.chunkSizeInput)).toHaveValue('500');
    await expect(page.getByTestId(TestIds.chunkOverlapInput)).toHaveValue('50');

    // Navigation in preview
    await expect(page.getByText('Jonathan Harker travels to Transylvania')).toBeVisible();
    await page.getByTestId(TestIds.previewDialogNextButton).click();
    await expect(page.getByText('vows to stop Dracula’s growing threat.')).toBeVisible();
    await page.getByTestId(TestIds.previewDialogNextButton).click();
    await expect(page.getByText('In the final confrontation, the hunters intercept Dracula’s caravan')).toBeVisible();
    await page.getByTestId(TestIds.previewDialogPrevButton).click();
   // await expect(page.getByText('vows to stop Dracula’s growing threat.')).toBeVisible();

    // Final Import
    await page.getByTestId(TestIds.previewDialogImportButton).click();

    // Verify import completed (progress bar hidden and chunks shown)
    await expect(page.getByTestId(TestIds.importProgress)).not.toBeVisible();
    await expect(page.getByTestId(TestIds.chunkCountText)).toBeVisible();
    await expect(page.getByTestId(TestIds.chunkCountText)).toContainText('Count: 6');
  });

  await test.step('2. Import and remove files', async () => {
    const collectionItem = page.getByTestId(`${TestIds.collectionItem}-Dracula_2`);
    await expect(collectionItem).toBeVisible();
    await collectionItem.click();
            
    await page.getByTestId(TestIds.importStep1Button).click();

    // Pick File
    await page.locator('input[type="file"]').setInputFiles(filePath);
    await page.getByTestId(TestIds.importFileSubmitButton).click();

    // Verify step 2 button shown
    await expect(page.getByTestId(TestIds.importStep2Button)).toBeVisible({ timeout: 5000 });

    // 4. Delete Files
    await page.getByTestId(TestIds.deleteFilesButton).click();
    await page.getByTestId(TestIds.deleteConfirmButton).click();

    // Verify step 2 button hidden
    await expect(page.getByTestId(TestIds.importStep2Button)).not.toBeVisible();
  });

  await test.step('3. Inspect collection', async () => {
    // 1. Select Collection
    const collectionItem = page.getByTestId(`${TestIds.collectionItem}-Dracula_2`);
    await expect(collectionItem).toBeVisible();
    await collectionItem.click();

    // 2. Open Inspect Dialog
    await page.getByTestId(TestIds.inspectButton).click();
    await expect(page.getByTestId(TestIds.inspectDialogTitle)).toBeVisible();

    // 3. Navigation in Inspect Tab
    await expect(page.getByText('Jonathan Harker travels to Transylvania')).toBeVisible();
    await page.getByTestId(TestIds.inspectNextButton).click();
    await expect(page.getByText('vows to stop Dracula’s growing threat.')).toBeVisible();
    await page.getByTestId(TestIds.inspectNextButton).click();
    await expect(page.getByText('In the final confrontation, the hunters intercept Dracula’s caravan')).toBeVisible();
    await page.getByTestId(TestIds.inspectNextButton).click();
    await expect(page.getByText('Mina’s friend whose tragic transformation')).toBeVisible()
    await page.getByTestId(TestIds.inspectPrevButton).click();
    await expect(page.getByText('In the final confrontation, the hunters intercept Dracula’s caravan')).toBeVisible();

    // 4. Switch to Query Tab
    await page.getByTestId(TestIds.queryTab).click();

    // 5. Run Query
    const queryInput = page.getByTestId(TestIds.queryInput);
    await queryInput.fill('Mina curse');
    await page.getByTestId(TestIds.querySendButton).click();

    // 6. Navigate Query Results (if multiple)
    await expect(page.getByText('Mina becomes a target')).toBeVisible();
    const nextDocButton = page.getByTestId(TestIds.queryNextDocButton);
    await nextDocButton.click();
    await expect(page.getByText('His death frees Mina from the curse')).toBeVisible();
    

    // 7. Close Dialog
    await page.getByTestId(TestIds.inspectCloseButton).click();
    await expect(page.getByTestId(TestIds.inspectDialogTitle)).not.toBeVisible();
  });

  await test.step('4. Delete collection', async () => {
    const collectionItem = page.getByTestId(`${TestIds.collectionItem}-Dracula_2`);
    await expect(collectionItem).toBeVisible();
    await collectionItem.click();

    await page.getByTestId(TestIds.deleteCollectionButton).click();
    await page.getByTestId(TestIds.deleteConfirmButton).click();
    await expect(collectionItem).not.toBeVisible();
  });
});
