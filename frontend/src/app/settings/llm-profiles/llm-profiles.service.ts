import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { getApiUrl } from '../../../environments/runtime-config';
import {
  LlmProfile,
  LlmProfileCreatePayload,
  LlmProfileTestResult,
  LlmProfileUpdatePayload,
  LlmProvider,
} from './llm-profile.models';

@Injectable({ providedIn: 'root' })
export class LlmProfilesService {
  private readonly baseUrl = `${getApiUrl()}/agent`;

  constructor(private readonly http: HttpClient) {}

  listProviders(): Promise<LlmProvider[]> {
    return firstValueFrom(this.http.get<LlmProvider[]>(`${this.baseUrl}/providers`));
  }

  listProfiles(): Promise<LlmProfile[]> {
    return firstValueFrom(this.http.get<LlmProfile[]>(`${this.baseUrl}/profiles`));
  }

  createProfile(payload: LlmProfileCreatePayload): Promise<LlmProfile> {
    return firstValueFrom(this.http.post<LlmProfile>(`${this.baseUrl}/profiles`, payload));
  }

  updateProfile(id: string, payload: LlmProfileUpdatePayload): Promise<LlmProfile> {
    return firstValueFrom(
      this.http.patch<LlmProfile>(`${this.baseUrl}/profiles/${id}`, payload)
    );
  }

  async deleteProfile(id: string): Promise<void> {
    await firstValueFrom(this.http.delete<void>(`${this.baseUrl}/profiles/${id}`));
  }

  activateProfile(id: string, active: boolean): Promise<LlmProfile> {
    return firstValueFrom(
      this.http.post<LlmProfile>(`${this.baseUrl}/profiles/${id}/activate`, { active })
    );
  }

  testProfile(id: string): Promise<LlmProfileTestResult> {
    return firstValueFrom(
      this.http.post<LlmProfileTestResult>(`${this.baseUrl}/profiles/${id}/test`, {})
    );
  }
}
