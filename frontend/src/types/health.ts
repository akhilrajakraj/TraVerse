export interface HealthCheckResult {
  status: "healthy" | string;
  services: {
    database: "healthy" | string;
    redis: "healthy" | string;
    django: "healthy" | string;
  };
}
