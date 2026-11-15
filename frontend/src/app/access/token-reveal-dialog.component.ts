import { Component, Inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { TestIds } from '../testing/test-ids';

@Component({
  selector: 'app-token-reveal-dialog',
  standalone: true,
  imports: [MatButtonModule, MatDialogModule, MatIconModule],
  template: `
    <h2 mat-dialog-title>Copy your token now</h2>
    <div mat-dialog-content>
      <p class="warning">
        This token is shown only once. Store it somewhere safe before closing
        this dialog.
      </p>
      <code class="token" [attr.data-testid]="TestIds.tokenRevealValue">{{
        data.token
      }}</code>
    </div>
    <div mat-dialog-actions align="end">
      <button mat-button type="button" (click)="copy()">
        <mat-icon>{{ copied ? 'check' : 'content_copy' }}</mat-icon>
        {{ copied ? 'Copied' : 'Copy' }}
      </button>
      <button mat-flat-button color="primary" mat-dialog-close>Done</button>
    </div>
  `,
  styles: [
    `
      .warning {
        color: #8a4b00;
        background: #fff4e5;
        border-radius: 8px;
        padding: 10px 12px;
      }
      .token {
        display: block;
        padding: 14px;
        border-radius: 8px;
        background: #f1f4f8;
        color: #14324f;
        font-size: 13px;
        word-break: break-all;
        user-select: all;
      }
    `,
  ],
})
export class TokenRevealDialogComponent {
  protected readonly TestIds = TestIds;
  copied = false;

  constructor(@Inject(MAT_DIALOG_DATA) public data: { token: string }) {}

  async copy(): Promise<void> {
    await navigator.clipboard.writeText(this.data.token);
    this.copied = true;
  }
}
