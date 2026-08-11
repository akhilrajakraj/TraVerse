import { apiRequest } from "../../../lib/apiClient";

export interface AuthTokens { access: string; refresh: string; }
export interface User { id: string; email: string; first_name: string; last_name: string; is_active: boolean; date_joined: string; }

export function login(email: string, password: string) {
  return apiRequest<AuthTokens>("/api/accounts/login/", { method: "POST", body: JSON.stringify({ email, password }) });
}

export function register(email: string, password: string, firstName: string, lastName: string) {
  return apiRequest<User>("/api/accounts/register/", { method: "POST", body: JSON.stringify({ email, password, first_name: firstName, last_name: lastName }) });
}

export function me() { return apiRequest<User>("/api/accounts/me/"); }
export function logout() { return apiRequest<void>("/api/accounts/logout/", { method: "POST" }); }
