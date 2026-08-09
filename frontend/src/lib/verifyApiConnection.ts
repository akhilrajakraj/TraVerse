import type { HealthCheckResult } from "../types/health";

const API_ROOT_SUFFIX = /\/api\/v1\/?$/;

export function getApiBaseUrl(): string {
  const configured = import.meta.env.VITE_API_BASE_URL?.trim();
  if (!configured) {
    throw new Error("VITE_API_BASE_URL is not configured.");
  }
  return configured.replace(/\/$/, "");
}

function getHealthUrl(baseUrl: string): string {
  return `${baseUrl.replace(API_ROOT_SUFFIX, "")}/health/`;
}

export async function verifyApiConnection(
  baseUrl = getApiBaseUrl(),
): Promise<HealthCheckResult> {
  const response = await fetch(getHealthUrl(baseUrl), {
    method: "GET",
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }

  const data: unknown = await response.json();
  if (!isHealthCheckResult(data)) {
    throw new Error("Health check returned an unexpected response shape.");
  }

  if (data.status !== "healthy") {
    throw new Error(
      `Backend reachable but unhealthy: database=${data.services.database}, redis=${data.services.redis}, django=${data.services.django}`,
    );
  }

  return data;
}

function isHealthCheckResult(value: unknown): value is HealthCheckResult {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Record<string, unknown>;
  const services = candidate.services;
  if (!services || typeof services !== "object") return false;

  const serviceValues = services as Record<string, unknown>;
  return (
    typeof candidate.status === "string" &&
    serviceValues.database === "healthy" &&
    serviceValues.redis === "healthy" &&
    serviceValues.django === "healthy"
  );
}
