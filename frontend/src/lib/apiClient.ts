const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, "") ?? "";

export interface ApiErrorShape { code: string; message: string; }

export class ApiRequestError extends Error {
  constructor(readonly status: number, readonly code: string, message: string) {
    super(message);
    this.name = "ApiRequestError";
  }
}

const ACCESS_KEY = "access_token";
const REFRESH_KEY = "refresh_token";
let refreshPromise: Promise<string> | null = null;

export function getAccessToken() { return localStorage.getItem(ACCESS_KEY); }
export function getRefreshToken() { return localStorage.getItem(REFRESH_KEY); }
export function setTokens(access: string, refresh?: string) {
  localStorage.setItem(ACCESS_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
}
export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

async function refreshAccessToken(): Promise<string> {
  if (refreshPromise) return refreshPromise;
  const refresh = getRefreshToken();
  if (!refresh) throw new ApiRequestError(401, "session_expired", "Your session has expired.");

  refreshPromise = fetch(`${API_BASE_URL}/api/accounts/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  }).then(async (response) => {
    if (!response.ok) throw new Error("Refresh failed");
    const data = (await response.json()) as { access: string; refresh?: string };
    setTokens(data.access, data.refresh);
    return data.access;
  }).finally(() => { refreshPromise = null; });

  return refreshPromise;
}

export async function apiRequest<T>(path: string, options: RequestInit = {}, retry = false): Promise<T> {
  const token = getAccessToken();
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });

  if (response.status === 401 && !retry && getRefreshToken()) {
    try {
      await refreshAccessToken();
      return apiRequest<T>(path, options, true);
    } catch {
      clearTokens();
      throw new ApiRequestError(401, "session_expired", "Your session has expired. Please log in again.");
    }
  }

  if (!response.ok) {
    let body: unknown = null;
    try { body = await response.json(); } catch { /* non-JSON response */ }
    const candidate = body as { errors?: { code?: string; message?: string } | string; detail?: string } | null;
    const errors = candidate?.errors;
    const code = typeof errors === "object" && errors && typeof errors.code === "string" ? errors.code : "request_failed";
    const message = typeof errors === "object" && errors ? errors.message ?? `Request failed with status ${response.status}` : typeof errors === "string" ? errors : candidate?.detail ?? `Request failed with status ${response.status}`;
    throw new ApiRequestError(response.status, code, message);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
