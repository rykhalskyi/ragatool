import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { ApiToken, AuthService } from '../auth/auth.service';
import { DeleteConfirmationDialogComponent } from '../delete-confirmation-dialog/delete-confirmation-dialog.component';
import { TestIds } from '../testing/test-ids';
import { TokenCreateDialogComponent } from './token-create-dialog.component';
import { TokenRevealDialogComponent } from './token-reveal-dialog.component';

@Component({
  selector: 'app-access',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatIconModule,
    MatSnackBarModule,
    MatTableModule,
    MatTooltipModule,
  ],
  templateUrl: './access.component.html',
  styleUrl: './access.component.scss',
})
export class AccessComponent implements OnInit {
  protected readonly TestIds = TestIds;
  readonly columns = ['name', 'prefix', 'created', 'lastUsed', 'status', 'actions'];

  tokens: ApiToken[] = [];
  loading = false;
  error = '';

  constructor(
    private readonly auth: AuthService,
    private readonly dialog: MatDialog,
    private readonly snackBar: MatSnackBar,
    private readonly router: Router
  ) {}

  ngOnInit(): void {
    void this.loadTokens();
  }

  async loadTokens(): Promise<void> {
    this.loading = true;
    this.error = '';
    try {
      this.tokens = await this.auth.listTokens();
    } catch {
      this.error = 'Could not load API tokens.';
    } finally {
      this.loading = false;
    }
  }

  async createToken(): Promise<void> {
    const dialogRef = this.dialog.open(TokenCreateDialogComponent, {
      width: '420px',
    });
    const name = await firstValueFrom(dialogRef.afterClosed());
    if (!name) {
      return;
    }

    try {
      const created = await this.auth.createToken(name);
      this.dialog.open(TokenRevealDialogComponent, {
        width: '560px',
        data: { token: created.token },
        disableClose: true,
      });
      await this.loadTokens();
    } catch {
      this.snackBar.open('Could not create the token.', 'Dismiss', {
        duration: 4000,
      });
    }
  }

  async revokeToken(token: ApiToken): Promise<void> {
    const dialogRef = this.dialog.open(DeleteConfirmationDialogComponent, {
      data: {
        title: 'Revoke token',
        message: `Revoke "${token.name}"? Any client using it will lose access immediately.`,
      },
    });
    const confirmed = await firstValueFrom(dialogRef.afterClosed());
    if (!confirmed) {
      return;
    }

    try {
      await this.auth.revokeToken(token.id);
      await this.loadTokens();
    } catch {
      this.snackBar.open('Could not revoke the token.', 'Dismiss', {
        duration: 4000,
      });
    }
  }

  async logout(): Promise<void> {
    await this.auth.logout();
    await this.router.navigate(['/login']);
  }
}
