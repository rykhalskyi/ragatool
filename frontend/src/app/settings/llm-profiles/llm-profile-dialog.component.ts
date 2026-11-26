import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, Inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { TestIds } from '../../testing/test-ids';
import { LlmProfilesService } from './llm-profiles.service';
import { LlmProfile, LlmProvider } from './llm-profile.models';

export interface LlmProfileDialogData {
  profile: LlmProfile | null;
  providers: LlmProvider[];
}

@Component({
  selector: 'app-llm-profile-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
  ],
  templateUrl: './llm-profile-dialog.component.html',
  styleUrl: './llm-profile-dialog.component.scss',
})
export class LlmProfileDialogComponent {
  protected readonly TestIds = TestIds;

  name = '';
  provider = 'openai';
  baseUrl = '';
  model = '';
  apiKey = '';
  temperature = 0.2;
  maxTokens = 2048;
  connectTimeoutSeconds = 30;
  readTimeoutSeconds = 120;
  showAdvanced = false;
  submitting = false;
  error = '';

  readonly isEditing: boolean;

  constructor(
    private readonly dialogRef: MatDialogRef<LlmProfileDialogComponent, LlmProfile | undefined>,
    @Inject(MAT_DIALOG_DATA) readonly data: LlmProfileDialogData,
    private readonly profilesService: LlmProfilesService
  ) {
    this.isEditing = data.profile !== null;

    if (data.profile) {
      this.name = data.profile.name;
      this.provider = data.profile.provider;
      this.baseUrl = data.profile.base_url;
      this.model = data.profile.model;
      this.temperature = data.profile.temperature;
      this.maxTokens = data.profile.max_tokens;
      this.connectTimeoutSeconds = data.profile.connect_timeout_seconds;
      this.readTimeoutSeconds = data.profile.read_timeout_seconds;
    } else {
      this.applyProviderDefaults(data.providers[0]);
    }
  }

  get canSubmit(): boolean {
    if (this.submitting) {
      return false;
    }
    if (!this.name.trim() || !this.baseUrl.trim() || !this.model.trim()) {
      return false;
    }
    return this.isEditing || this.apiKey.trim().length > 0;
  }

  onProviderChange(providerId: string): void {
    this.provider = providerId;
    const provider = this.data.providers.find((item) => item.id === providerId);
    if (!provider) {
      return;
    }

    const isKnownBaseUrl = this.data.providers.some(
      (item) => item.default_base_url === this.baseUrl.trim()
    );
    const isKnownModel = this.data.providers.some(
      (item) => item.default_model === this.model.trim()
    );
    if (!this.baseUrl.trim() || isKnownBaseUrl) {
      this.baseUrl = provider.default_base_url;
    }
    if (!this.model.trim() || isKnownModel) {
      this.model = provider.default_model;
    }
  }

  cancel(): void {
    this.dialogRef.close();
  }

  async submit(): Promise<void> {
    if (!this.canSubmit) {
      return;
    }

    this.submitting = true;
    this.error = '';
    try {
      const profile = this.isEditing && this.data.profile
        ? await this.profilesService.updateProfile(this.data.profile.id, {
            name: this.name.trim(),
            provider: this.provider,
            base_url: this.baseUrl.trim(),
            model: this.model.trim(),
            temperature: this.temperature,
            max_tokens: this.maxTokens,
            connect_timeout_seconds: this.connectTimeoutSeconds,
            read_timeout_seconds: this.readTimeoutSeconds,
            ...(this.apiKey.trim() ? { api_key: this.apiKey.trim() } : {}),
          })
        : await this.profilesService.createProfile({
            name: this.name.trim(),
            provider: this.provider,
            base_url: this.baseUrl.trim(),
            api_key: this.apiKey.trim(),
            model: this.model.trim(),
            temperature: this.temperature,
            max_tokens: this.maxTokens,
            connect_timeout_seconds: this.connectTimeoutSeconds,
            read_timeout_seconds: this.readTimeoutSeconds,
          });

      this.dialogRef.close(profile);
    } catch (error) {
      this.error = this.errorMessage(error);
    } finally {
      this.submitting = false;
    }
  }

  private applyProviderDefaults(provider: LlmProvider | undefined): void {
    if (!provider) {
      return;
    }
    this.provider = provider.id;
    this.baseUrl = provider.default_base_url;
    this.model = provider.default_model;
  }

  private errorMessage(error: unknown): string {
    if (error instanceof HttpErrorResponse) {
      const detail = (error.error as { detail?: unknown } | null)?.detail;
      if (typeof detail === 'string' && detail.trim()) {
        return detail;
      }
    }
    return 'Could not save the LLM profile.';
  }
}
