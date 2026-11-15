import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { Router } from '@angular/router';
import { AuthService } from '../auth/auth.service';
import { TestIds } from '../testing/test-ids';

@Component({
  selector: 'app-setup',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatCardModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
  ],
  templateUrl: './setup.component.html',
  styleUrl: './setup.component.scss',
})
export class SetupComponent {
  protected readonly TestIds = TestIds;

  username = 'admin';
  password = '';
  confirmPassword = '';
  setupCode = '';
  hidePassword = true;
  loading = false;
  error = '';

  constructor(
    private readonly auth: AuthService,
    private readonly router: Router
  ) {}

  async submit(): Promise<void> {
    this.error = '';

    if (!this.username || !this.setupCode || !this.password) {
      this.error = 'Fill in every field.';
      return;
    }
    if (this.password.length < 8) {
      this.error = 'Password must be at least 8 characters.';
      return;
    }
    if (this.password !== this.confirmPassword) {
      this.error = 'Passwords do not match.';
      return;
    }
    if (this.loading) {
      return;
    }

    this.loading = true;
    try {
      await this.auth.setup(
        this.username.trim(),
        this.password,
        this.setupCode.trim()
      );
      await this.router.navigate(['/']);
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        if (error.status === 400) {
          this.error = 'That setup code is not valid. Check the backend logs.';
        } else if (error.status === 409) {
          await this.router.navigate(['/login']);
        } else if (error.status === 403) {
          this.error = 'This origin is not allowed to complete setup.';
        } else {
          this.error = 'Setup failed. Please try again.';
        }
      } else {
        this.error = 'Could not reach the Ragatool server.';
      }
    } finally {
      this.loading = false;
    }
  }
}
