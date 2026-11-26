import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSnackBar } from '@angular/material/snack-bar';
import { firstValueFrom } from 'rxjs';
import { DeleteConfirmationDialogComponent } from '../../delete-confirmation-dialog/delete-confirmation-dialog.component';
import { TestIds } from '../../testing/test-ids';
import {
  LlmProfileDialogComponent,
  LlmProfileDialogData,
} from './llm-profile-dialog.component';
import { LlmProfile, LlmProvider } from './llm-profile.models';
import { LlmProfilesService } from './llm-profiles.service';

@Component({
  selector: 'app-llm-profiles',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatIconModule,
    MatSlideToggleModule,
  ],
  templateUrl: './llm-profiles.component.html',
  styleUrl: './llm-profiles.component.scss',
})
export class LlmProfilesComponent implements OnInit {
  protected readonly TestIds = TestIds;

  providers: LlmProvider[] = [];
  profiles: LlmProfile[] = [];
  loading = false;
  error = '';
  busyId: string | null = null;
  testingId: string | null = null;

  constructor(
    private readonly profilesService: LlmProfilesService,
    private readonly dialog: MatDialog,
    private readonly snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    void this.load();
  }

  async load(): Promise<void> {
    this.loading = true;
    this.error = '';
    try {
      const [providers, profiles] = await Promise.all([
        this.profilesService.listProviders(),
        this.profilesService.listProfiles(),
      ]);
      this.providers = providers;
      this.profiles = profiles;
    } catch {
      this.error = 'Could not load LLM profiles.';
    } finally {
      this.loading = false;
    }
  }

  providerLabel(profile: LlmProfile): string {
    return this.providers.find((item) => item.id === profile.provider)?.label
      ?? profile.provider;
  }

  openCreate(): void {
    this.openDialog(null);
  }

  openEdit(profile: LlmProfile): void {
    this.openDialog(profile);
  }

  private openDialog(profile: LlmProfile | null): void {
    const data: LlmProfileDialogData = { profile, providers: this.providers };
    this.dialog
      .open(LlmProfileDialogComponent, { width: '560px', data })
      .afterClosed()
      .subscribe((result: LlmProfile | undefined) => {
        if (result) {
          void this.load();
        }
      });
  }

  async activate(profile: LlmProfile): Promise<void> {
    if (this.busyId) {
      return;
    }
    this.busyId = profile.id;
    try {
      await this.profilesService.activateProfile(profile.id, !profile.is_active);
      await this.load();
    } catch {
      this.snackBar.open('Could not update the active profile.', 'Dismiss', {
        duration: 4000,
      });
    } finally {
      this.busyId = null;
    }
  }

  async test(profile: LlmProfile): Promise<void> {
    if (this.testingId) {
      return;
    }
    this.testingId = profile.id;
    try {
      const result = await this.profilesService.testProfile(profile.id);
      const suffix = result.latency_ms !== null ? ` (${result.latency_ms} ms)` : '';
      this.snackBar.open(`${result.message}${suffix}`, 'Dismiss', {
        duration: 5000,
      });
    } catch (error) {
      this.snackBar.open(this.errorMessage(error, 'The connection test failed.'), 'Dismiss', {
        duration: 5000,
      });
    } finally {
      this.testingId = null;
    }
  }

  async remove(profile: LlmProfile): Promise<void> {
    const confirmed = await firstValueFrom(
      this.dialog
        .open(DeleteConfirmationDialogComponent, {
          data: {
            title: 'Delete LLM profile',
            message: `Delete "${profile.name}"? The stored API key will be removed.`,
          },
        })
        .afterClosed()
    );
    if (!confirmed) {
      return;
    }

    this.busyId = profile.id;
    try {
      await this.profilesService.deleteProfile(profile.id);
      await this.load();
    } catch {
      this.snackBar.open('Could not delete the LLM profile.', 'Dismiss', {
        duration: 4000,
      });
    } finally {
      this.busyId = null;
    }
  }

  private errorMessage(error: unknown, fallback: string): string {
    if (error instanceof HttpErrorResponse) {
      const detail = (error.error as { detail?: unknown } | null)?.detail;
      if (typeof detail === 'string' && detail.trim()) {
        return detail;
      }
    }
    return fallback;
  }
}
