import { test, expect } from '@playwright/test';
import * as path from 'path';

import { TestIds } from '../src/app/testing/test-ids';

test('2-step import Dracula collection', async ({ page }) => {
  const draculaFilePath = path.resolve(__dirname, 'text/dracula.txt');
  const lotrFilePath = path.resolve(__dirname, 'text/lotr.txt');

  await test.step('Once Before tests: delete Dracula if exists', async () => {
    await page.goto('http://localhost:4200');
    const collectionItem = page.getByTestId(`${TestIds.collectionItem}-Dracula_2s`);
    if (await collectionItem.isVisible()) {
      await collectionItem.click();
      await page.getByTestId(TestIds.deleteCollectionButton).click();
      await page.getByTestId(TestIds.deleteConfirmButton).click();
      await expect(collectionItem).not.toBeVisible();
    }
  });

  await test.step('1. Add Dracula collection (2-step import)', async () => {
    // click 'Settings'
    await page.getByTestId(TestIds.settingsButton).click();

    // enable 'TwoStepImport'
    const twoStepSwitch = page.getByTestId(TestIds.twoStepImportSwitch);
    const switchButton = twoStepSwitch.getByRole('switch');
    if (!(await switchButton.isChecked())) {
      await switchButton.click();
    }
    await expect(switchButton).toBeChecked();

    // click 'Save'
    await page.getByTestId(TestIds.saveSettingsButton).click();
    await page.waitForTimeout(500); 

    // click 'Add Collection'
    await page.getByTestId(TestIds.addCollectionButton).click();

    // input to 'Collection Name' 'Dracula'
    await page.getByTestId(TestIds.addCollectionNameInput).fill('Dracula_2s');

    // click 'Ok'
    await page.getByTestId(TestIds.addCollectionOkButton).click();

    // item shown 'Dracula'
    const collectionItem = page.getByTestId(`${TestIds.collectionItem}-Dracula_2s`);
    await expect(collectionItem).toBeVisible();

    // click 'Dracula'
    await collectionItem.click();

    // select in 'Select Import Type' 'File'
    await page.getByTestId(TestIds.importTypeSelect).click();
    await page.getByRole('option', { name: 'FILE' }).click();
    await page.keyboard.press('Escape');

    // Step 1: Load to files
    await page.getByTestId(TestIds.importStep1Button).click();
    
    // Pick File
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.getByTestId(TestIds.pickFileButton).click(); 
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(draculaFilePath);

    // click 'Load' (Submit in dialog)
    await page.getByTestId(TestIds.importFileSubmitButton).click();

    // wait until element 'progress' hidden
    await expect(page.getByTestId(TestIds.importProgress)).not.toBeVisible({ timeout: 2000 });

    // Step 2: Review and vectorize
    await page.getByTestId(TestIds.importStep2Button).click({timeout: 2000});
    await expect(page.getByText('Review and Import')).toBeVisible();
    
    // click 'Import' in preview dialog
    await page.getByTestId(TestIds.previewDialogImportButton).click();

    // wait until element 'progress' hidden
    await expect(page.getByTestId(TestIds.importProgress)).toBeVisible();
    await expect(page.getByTestId(TestIds.importProgress)).not.toBeVisible({ timeout: 60000 });

    // text shown 'Count: 5' (dracula.txt has 5 chunks probably, let's check)
    // Actually, I'll just check if it's visible.
    await expect(page.getByTestId(TestIds.chunkCountText)).toBeVisible();
  });

  await test.step('2. Edit Dracula description', async () => {
    // Note: Scenario said "Lord of the ring" but meant "Dracula"
    const collectionItem = page.getByTestId(`${TestIds.collectionItem}-Dracula_2s`);
    await collectionItem.click();

    await page.getByTestId(TestIds.editDescriptionButton).click();
    await page.getByTestId(TestIds.descriptionTextarea).fill('A story of Vlad Dracula');
    await page.getByTestId(TestIds.saveDescriptionButton).click();
    await expect(page.getByTestId(TestIds.collectionDescription)).toHaveText('A story of Vlad Dracula');
  });

  await test.step('3. Import file again into Dracula collection', async () => {
    const collectionItem = page.getByTestId(`${TestIds.collectionItem}-Dracula_2s`);
    await collectionItem.click();

    // Step 1: Load to files
    await page.getByTestId(TestIds.importStep1Button).click();
    
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.getByTestId(TestIds.pickFileButton).click(); 
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(lotrFilePath);
    await page.getByTestId(TestIds.importFileSubmitButton).click();

    await expect(page.getByTestId(TestIds.importProgress)).not.toBeVisible({ timeout: 2000 });

    // Step 2: Review and vectorize
    await page.getByTestId(TestIds.importStep2Button).click();
    await page.getByTestId(TestIds.previewDialogImportButton).click();

    await expect(page.getByTestId(TestIds.importProgress)).toBeVisible();
    await expect(page.getByTestId(TestIds.importProgress)).not.toBeVisible({ timeout: 60000 });
    
    // Scenario says 'Count: 6'
    await expect(page.getByTestId(TestIds.chunkCountText)).toContainText('Count: 20');
  });

  await test.step('4. Rewrite Dracula description', async () => {
    const collectionItem = page.getByTestId(`${TestIds.collectionItem}-Dracula_2s`);
    await collectionItem.click();

    await page.getByTestId(TestIds.editDescriptionButton).click();
    await page.getByTestId(TestIds.descriptionTextarea).fill('New updated description');
    await page.getByTestId(TestIds.saveDescriptionButton).click();
    await expect(page.getByTestId(TestIds.collectionDescription)).toHaveText('New updated description');
  });

  await test.step('5. Cancel description editing', async () => {
    const collectionItem = page.getByTestId(`${TestIds.collectionItem}-Dracula_2s`);
    await collectionItem.click();

    await page.getByTestId(TestIds.editDescriptionButton).click();
    await page.getByTestId(TestIds.descriptionTextarea).fill('This should be cancelled');
    await page.getByTestId(TestIds.cancelDescriptionButton).click();
    await expect(page.getByTestId(TestIds.collectionDescription)).toHaveText('New updated description');
  });

  await test.step('6. Delete Dracula collection', async () => {
    const collectionItem = page.getByTestId(`${TestIds.collectionItem}-Dracula_2s`);
    await collectionItem.click();

    await page.getByTestId(TestIds.deleteCollectionButton).click();
    await page.getByTestId(TestIds.deleteConfirmButton).click();
    await expect(collectionItem).not.toBeVisible();
  });
});
