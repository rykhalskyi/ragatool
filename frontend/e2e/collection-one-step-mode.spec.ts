import { test, expect } from '@playwright/test';
import * as path from 'path';

import { TestIds } from '@testing/test-ids';

test('Add Lord of the Rings collection and import file', async ({ page }) => {
  const lotrFilePath = path.resolve(__dirname, 'text/lotr.txt');

  await test.step('Once Before tests: delete Lord of the Rings if exists', async () => {
    await page.goto('http://localhost:4200');
    const collectionItem = page.getByTestId(`${TestIds.collectionItem}-Lord of the Rings`);
    if (await collectionItem.isVisible()) {
      await collectionItem.click();
      await page.getByTestId(TestIds.deleteCollectionButton).click();
      await page.getByTestId(TestIds.deleteConfirmButton).click();
      await expect(collectionItem).not.toBeVisible();
    }
  });

  await test.step('1. Add Lord of the ring collection', async () => {
    // click 'Settings'
    await page.getByTestId(TestIds.settingsButton).click();

    // disable 'TwoStepImport'
    const twoStepSwitch = page.getByTestId(TestIds.twoStepImportSwitch);
    const switchButton = twoStepSwitch.getByRole('switch');
    if (await switchButton.isChecked()) {
      await switchButton.click();
    }
    await expect(switchButton).not.toBeChecked();

    // click 'Save'
    await page.getByTestId(TestIds.saveSettingsButton).click();
    await page.waitForTimeout(500); 

    // click 'Add Collection'
    await page.getByTestId(TestIds.addCollectionButton).click();

    // popup shown 'Add New Collection'
    await expect(page.getByTestId(TestIds.addCollectionDialogTitle)).toBeVisible();

    // input to 'Collection Name' 'Lord of the Rings'
    await page.getByTestId(TestIds.addCollectionNameInput).fill('Lord of the Rings');

    // click 'Ok'
    await page.getByTestId(TestIds.addCollectionOkButton).click();

    // popup hidden
    await expect(page.getByTestId(TestIds.addCollectionDialogTitle)).not.toBeVisible();

    // item shown 'Lord Of the Ring'
    const collectionItem = page.getByTestId(`${TestIds.collectionItem}-Lord of the Rings`);
    await expect(collectionItem).toBeVisible();

    // click 'Lord Of the Ring'
    await collectionItem.click();

    // Wait for collection page to load
    await expect(page).toHaveURL(/\/collection\/.*/);

    // select in 'Select Import Type' 'File'
    await page.getByTestId(TestIds.importTypeSelect).click();
    await page.getByRole('option', { name: 'FILE' }).click();
    await page.keyboard.press('Escape');

    // click 'Import'
    await page.getByTestId(TestIds.importButton).click();

    // popup shown 'Import File to Lord of the Rings'
    await expect(page.getByText('Import File to Lord of the Rings')).toBeVisible();

    // click 'Pickfile'
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.getByTestId(TestIds.pickFileButton).click(); 
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(lotrFilePath);

    // click 'Import' (Submit in dialog)
    await page.getByTestId(TestIds.importFileSubmitButton).click();

    // element shown 'progress'
    await expect(page.getByTestId(TestIds.importProgress)).toBeVisible();

    // wait until element 'progress' hidden
    await expect(page.getByTestId(TestIds.importProgress)).not.toBeVisible({ timeout: 60000 });

    // text shown 'Count: 11'
    await expect(page.getByTestId(TestIds.chunkCountText)).toContainText('Count: 11');

    const logItemsCount = await page.getByTestId(TestIds.logItem).count();
    await expect(logItemsCount).toBe(1);
  });

  await test.step('2. Edit Lord of the ring description', async () => {
    const collectionItem = page.getByTestId(`${TestIds.collectionItem}-Lord of the Rings`);
    await collectionItem.click();

    await page.getByTestId(TestIds.editDescriptionButton).click();
    await page.getByTestId(TestIds.descriptionTextarea).fill('A story of a ring.');
    await page.getByTestId(TestIds.saveDescriptionButton).click();
    await expect(page.getByTestId(TestIds.collectionDescription)).toHaveText('A story of a ring.');
  });

  await test.step('3. Import file again into Lord of the Rings collection', async () => {
    const collectionItem = page.getByTestId(`${TestIds.collectionItem}-Lord of the Rings`);
    await collectionItem.click();
    await page.getByTestId(TestIds.importButton).click();
    await expect(page.getByText('Import File to Lord of the Rings')).toBeVisible();

    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.getByTestId(TestIds.pickFileButton).click(); 
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(lotrFilePath);
    await page.getByTestId(TestIds.importFileSubmitButton).click();

    await expect(page.getByTestId(TestIds.importProgress)).toBeVisible();
    await expect(page.getByTestId(TestIds.importProgress)).not.toBeVisible({ timeout: 60000 });
    await expect(page.getByTestId(TestIds.chunkCountText)).toContainText('Count: 22');
    
    const logItemsCount = await page.getByTestId(TestIds.logItem).count();
    await expect(logItemsCount).toBe(2);
  });

  await test.step('4. Rewrite Lord of the Rings description', async () => {
    const collectionItem = page.getByTestId(`${TestIds.collectionItem}-Lord of the Rings`);
    await collectionItem.click();

    await page.getByTestId(TestIds.editDescriptionButton).click();
    await page.getByTestId(TestIds.descriptionTextarea).fill('New updated description');
    await page.getByTestId(TestIds.saveDescriptionButton).click();
    await expect(page.getByTestId(TestIds.collectionDescription)).toHaveText('New updated description');
  });

  await test.step('5. Cancel description editing', async () => {
    const collectionItem = page.getByTestId(`${TestIds.collectionItem}-Lord of the Rings`);
    await collectionItem.click();

    await page.getByTestId(TestIds.editDescriptionButton).click();
    await page.getByTestId(TestIds.descriptionTextarea).fill('This should be cancelled');
    await page.getByTestId(TestIds.cancelDescriptionButton).click();
    await expect(page.getByTestId(TestIds.collectionDescription)).toHaveText('New updated description');
  });

  await test.step('6. Delete Lord of the Rings collection', async () => {
    const collectionItem = page.getByTestId(`${TestIds.collectionItem}-Lord of the Rings`);
    await collectionItem.click();

    await page.getByTestId(TestIds.deleteCollectionButton).click();
    await page.getByTestId(TestIds.deleteConfirmButton).click();
    await expect(collectionItem).not.toBeVisible();
  });
});
