// Runtime configuration. The container entrypoint overwrites this file at start
// from the API_URL environment variable, so the same built image can be
// deployed anywhere without rebuilding the Angular bundle.
//
// A non-empty apiUrl wins. `null` falls back to the build-time environment
// value (used by `ng serve` and tests).
window.RAGATOUL_CONFIG = { apiUrl: null };
