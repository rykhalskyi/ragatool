import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { TestIds } from '../testing/test-ids';

@Component({
  selector: 'app-token-create-dialog',
  standalone: true,
  imports: [
    FormsModule,
    MatButtonModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
  ],
  template: `
    <h2 mat-dialog-title>Create API token</h2>
    <div mat-dialog-content>
      <p>Give the token a name so you can recognize it later.</p>
      <mat-form-field appearance="outline">
        <mat-label>Token name</mat-label>
        <input
          matInput
          name="name"
          [(ngModel)]="name"
          placeholder="opencode, thunderbird, ci…"
          [attr.data-testid]="TestIds.tokenNameInput"
          (keyup.enter)="submit()"
          cdkFocusInitial
        />
      </mat-form-field>
    </div>
    <div mat-dialog-actions align="end">
      <button mat-button mat-dialog-close>Cancel</button>
      <button
        mat-flat-button
        color="primary"
        [disabled]="!name.trim()"
        (click)="submit()"
        [attr.data-testid]="TestIds.tokenCreateSubmitButton"
      >
        Create
      </button>
    </div>
  `,
})
export class TokenCreateDialogComponent {
  protected readonly TestIds = TestIds;
  name = '';

  constructor(
    private readonly dialogRef: MatDialogRef<TokenCreateDialogComponent>
  ) {}

  submit(): void {
    const name = this.name.trim();
    if (name) {
      this.dialogRef.close(name);
    }
  }
}
