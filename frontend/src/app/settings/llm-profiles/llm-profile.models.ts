export interface LlmProvider {
  id: string;
  label: string;
  default_base_url: string;
  default_model: string;
  requires_api_key: boolean;
}

export interface LlmProfile {
  id: string;
  name: string;
  provider: string;
  base_url: string;
  model: string;
  temperature: number;
  max_tokens: number;
  connect_timeout_seconds: number;
  read_timeout_seconds: number;
  api_key_masked: string;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface LlmProfileCreatePayload {
  name: string;
  provider: string;
  base_url: string;
  api_key: string;
  model: string;
  temperature: number;
  max_tokens: number;
  connect_timeout_seconds: number;
  read_timeout_seconds: number;
  is_active?: boolean;
}

export interface LlmProfileUpdatePayload {
  name?: string;
  provider?: string;
  base_url?: string;
  api_key?: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  connect_timeout_seconds?: number;
  read_timeout_seconds?: number;
  is_active?: boolean;
}

export interface LlmProfileTestResult {
  ok: boolean;
  message: string;
  model: string | null;
  latency_ms: number | null;
}
