import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { SettingsService as ApiSettingsService } from './client/services/SettingsService';
import { Setting } from './client/models/Setting';
import { SettingCreate } from './client/models/SettingCreate';

@Injectable({
  providedIn: 'root'
})
export class SettingsService {
  private readonly _settings = new BehaviorSubject<Setting[]>([]);
  readonly settings$ = this._settings.asObservable();

  constructor() {
    this.loadSettings();
  }

  get settings(): Setting[] {
    return this._settings.getValue();
  }

  async loadSettings(): Promise<void> {
    try {
      const settings = await ApiSettingsService.readSettingsSettingsGet();      
      this._settings.next(settings);
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  }

  async updateSettings(settings: SettingCreate[]): Promise<void> {
    try {
      await ApiSettingsService.updateSettingsSettingsPut(settings);
      await this.loadSettings();
    } catch (error) {
      console.error('Error updating settings:', error);
      throw error; // re-throw to allow component to handle
    }
  }

  updateLocalSetting(updatedSetting: Setting): void {
    const currentSettings = this._settings.getValue();
    const settingIndex = currentSettings.findIndex(s => s.name === updatedSetting.name);
    if (settingIndex > -1) {
      const newSettings = [...currentSettings];
      newSettings[settingIndex] = updatedSetting;
      this._settings.next(newSettings);
    }
  }
}
