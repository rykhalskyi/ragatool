import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { getApiUrl } from '../../environments/runtime-config';

export interface AuthUser {
  id: string;
  username: string;
}

export interface AuthStatus {
  initialized: boolean;
}

export interface ApiToken {
  id: string;
  name: string;
  prefix: string;
  created_at: string | null;
  last_used_at: string | null;
  revoked_at: string | null;
}

export interface CreatedToken extends ApiToken {
  token: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = getApiUrl();

  private readonly _user = signal<AuthUser | null>(null);
  private readonly _initialized = signal<boolean | null>(null);

  readonly user = this._user.asReadonly();
  readonly initialized = this._initialized.asReadonly();
  readonly isAuthenticated = computed(() => this._user() !== null);

  async checkStatus(): Promise<boolean> {
    const status = await firstValueFrom(
      this.http.get<AuthStatus>(`${this.baseUrl}/auth/status`, {
        withCredentials: true,
      })
    );
    this._initialized.set(status.initialized);
    return status.initialized;
  }

  async login(username: string, password: string): Promise<AuthUser> {
    const user = await firstValueFrom(
      this.http.post<AuthUser>(
        `${this.baseUrl}/auth/login`,
        { username, password },
        { withCredentials: true }
      )
    );
    this._user.set(user);
    this._initialized.set(true);
    return user;
  }

  async setup(
    username: string,
    password: string,
    setupCode: string
  ): Promise<AuthUser> {
    const user = await firstValueFrom(
      this.http.post<AuthUser>(
        `${this.baseUrl}/auth/setup`,
        { username, password, setup_code: setupCode },
        { withCredentials: true }
      )
    );
    this._user.set(user);
    this._initialized.set(true);
    return user;
  }

  async me(): Promise<AuthUser> {
    try {
      const user = await firstValueFrom(
        this.http.get<AuthUser>(`${this.baseUrl}/auth/me`, {
          withCredentials: true,
        })
      );
      this._user.set(user);
      return user;
    } catch (error) {
      this._user.set(null);
      throw error;
    }
  }

  async logout(): Promise<void> {
    await firstValueFrom(
      this.http.post(`${this.baseUrl}/auth/logout`, {}, { withCredentials: true })
    );
    this._user.set(null);
  }

  async listTokens(): Promise<ApiToken[]> {
    return firstValueFrom(
      this.http.get<ApiToken[]>(`${this.baseUrl}/tokens`, {
        withCredentials: true,
      })
    );
  }

  async createToken(name: string): Promise<CreatedToken> {
    return firstValueFrom(
      this.http.post<CreatedToken>(
        `${this.baseUrl}/tokens`,
        { name },
        { withCredentials: true }
      )
    );
  }

  async revokeToken(id: string): Promise<void> {
    await firstValueFrom(
      this.http.delete(`${this.baseUrl}/tokens/${id}`, {
        withCredentials: true,
      })
    );
  }
}
