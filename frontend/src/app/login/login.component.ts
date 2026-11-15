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
  selector: 'app-login',
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
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
})
export class LoginComponent {
  protected readonly TestIds = TestIds;

  username = '';
  password = '';
  hidePassword = true;
  loading = false;
  error = '';

  constructor(
    private readonly auth: AuthService,
    private readonly router: Router
  ) {}

  async submit(): Promise<void> {
    if (!this.username || !this.password || this.loading) {
      return;
    }

    this.loading = true;
    this.error = '';
    try {
      await this.auth.login(this.username, this.password);
      await this.router.navigate(['/']);
    } catch (error) {
      if (error instanceof HttpErrorResponse && error.status === 401) {
        this.error = 'Invalid username or password.';
      } else if (error instanceof HttpErrorResponse && error.status === 429) {
        this.error = 'Too many login attempts. Please wait a minute and try again.';
      } else {
        this.error = 'Could not reach the Ragatool server.';
      }
    } finally {
      this.loading = false;
    }
  }
}
