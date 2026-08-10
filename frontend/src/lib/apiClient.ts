const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, "") ?? "http://localhost:8000";

export interface ApiErrorShape { code: string; message: string; }

export class ApiRequestError extends Error {
  constructor(readonly status: number, readonly code: string, message: string) {
    super(message);
    this.name = "ApiRequestError";
  }
}

function getAccessToken(): string | null {
  return localStorage.getItem("access_token");
}

export async function apiRequest<TResponse>(path: string, options: RequestInit = {}): Promise<TResponse> {
  const token = getAccessToken();
  const headers: HeadersInit = {
    Accept: "application/json",
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (!response.ok) {
    let body: { error?: ApiErrorShape } = {};
    try { body = await response.json(); } catch { /* non-JSON error */ }
    throw new ApiRequestError(response.status, body.error?.code ?? "unknown_error", body.error?.message ?? `Request failed with status ${response.status}`);
  }
  if (response.status === 204) return undefined as TResponse;
  return (await response.json()) as TResponse;
}