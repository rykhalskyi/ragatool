import { environment } from './environment';

interface RagatoolRuntimeConfig {
  apiUrl?: string | null;
}

declare global {
  interface Window {
    RAGATOUL_CONFIG?: RagatoolRuntimeConfig;
  }
}

/**
 * Resolve the backend base URL at runtime.
 *
 * The container entrypoint writes /config.js from the API_URL environment
 * variable, so deployments can point the same image at a different API address
 * without rebuilding. When no runtime value is present (local `ng serve`,
 * tests), fall back to the build-time environment.
 */
export function getApiUrl(): string {
  const runtimeUrl = window.RAGATOUL_CONFIG?.apiUrl;
  if (typeof runtimeUrl === 'string' && runtimeUrl.length > 0) {
    return runtimeUrl;
  }
  return environment.apiUrl;
}
