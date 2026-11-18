import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSelectModule } from '@angular/material/select';
import { MatIconModule } from '@angular/material/icon';
import { SettingsService } from '../settings.service';
import { Setting } from '../client/models/Setting';
import { SettingCreate } from '../client/models/SettingCreate';
import { Observable, of } from 'rxjs';
import { map } from 'rxjs/operators';
import { MatSnackBar } from '@angular/material/snack-bar';
import { TestIds } from '../testing/test-ids';
import { LlmProfilesComponent } from './llm-profiles/llm-profiles.component';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatSlideToggleModule,
    MatSelectModule,
    MatIconModule,
    LlmProfilesComponent
  ],
  templateUrl: './settings.component.html',
  styleUrl: './settings.component.scss'
})
export class SettingsComponent implements OnInit {
  protected readonly TestIds = TestIds;
  settings$: Observable<Setting[]> = of([]);
  private readonly selectOptions: Record<string, string[]> = {
    JsRenderMode: ['auto', 'always', 'off'],
  };
  private readonly hiddenSettings = new Set<string>(['UrlImportRecentFilters']);
  

  constructor(private settingsService: SettingsService, 
              private snackBar: MatSnackBar) {}

  ngOnInit(): void {
    this.settingsService.loadSettings();
    this.settings$ = this.settingsService.settings$.pipe(
      map(settings => settings.filter(setting => !this.hiddenSettings.has(setting.name)))
    );
  }

  updateSetting(setting: Setting, newValue: string) {
    const updatedSetting = { ...setting, value: newValue };
    this.settingsService.updateLocalSetting(updatedSetting);
  }

  async saveSettings() {
    const allSettings = this.settingsService.settings;
    const settingsToUpdate: SettingCreate[] = allSettings.map(({ name, value }) => ({ name, value }));

    try {
      await this.settingsService.updateSettings(settingsToUpdate);

      this.snackBar.open('Settings saved successfully!', 'Close', {
      duration: 3000, // auto close after 3 seconds
      horizontalPosition: 'right', // position in the corner
      verticalPosition: 'bottom',
    });
      // Optionally, provide user feedback that settings have been saved.
      console.log("All settings saved successfully!");
    } catch (error) {
      console.error("Failed to save all settings", error);
      // Optionally, provide user feedback about the error.
      alert("Failed to save settings. Please try again.");
    }
  }

  isNumeric(value: string): boolean {
    return value.trim() !== '' && !isNaN(parseFloat(value)) && isFinite(Number(value));
  }

  isBoolean(value: string): boolean {
    return value.toLowerCase() === 'true' || value.toLowerCase() === 'false';
  }

  isTrue(value: string): boolean {
    return value.toLowerCase() === 'true';
  }

  optionsFor(setting: Setting): string[] | null {
    return this.selectOptions[setting.name] ?? null;
  }

  minFor(setting: Setting): number {
    return ['MaxCrawlPages', 'RequestTimeoutSec', 'RetrievalFetchK'].includes(setting.name) ? 1 : 0;
  }

  testIdFor(setting: Setting): string | null {
    if (setting.name === 'TwoStepImport') {
      return this.TestIds.twoStepImportSwitch;
    }
    if (setting.name === 'RerankEnabled') {
      return this.TestIds.rerankEnabledSwitch;
    }
    if (setting.name === 'RetrievalFetchK') {
      return this.TestIds.retrievalFetchKInput;
    }
    if (setting.name === 'JsRenderMode') {
      return this.TestIds.jsRenderModeSelect;
    }
    return null;
  }

}
