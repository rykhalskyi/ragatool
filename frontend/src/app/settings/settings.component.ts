import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatIconModule } from '@angular/material/icon';
import { SettingsService } from '../settings.service';
import { Setting } from '../client/models/Setting';
import { SettingCreate } from '../client/models/SettingCreate';
import { Observable, of } from 'rxjs';
import { MatSnackBar } from '@angular/material/snack-bar';

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
    MatIconModule
  ],
  templateUrl: './settings.component.html',
  styleUrl: './settings.component.scss'
})
export class SettingsComponent implements OnInit {

  settings$: Observable<Setting[]> = of([]);
  

  constructor(private settingsService: SettingsService, 
              private snackBar: MatSnackBar) {}

  ngOnInit(): void {
    this.settingsService.loadSettings();
    this.settings$ = this.settingsService.settings$;
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
    return !isNaN(parseFloat(value)) && isFinite(Number(value));
  }

}
