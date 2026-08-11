import { apiClient } from "./client";

export const authApi = {
  me: <T = unknown>() => apiClient<T>("/api/v1/auth/me/"),
};
