import { useEffect, useState } from "react";

import { verifyApiConnection } from "../lib/verifyApiConnection";
import type { HealthCheckResult } from "../types/health";

const routes = ["/", "/login", "/register", "/destinations", "/trips"] as const;

type RoutePath = (typeof routes)[number];

function normalizePath(pathname: string): RoutePath {
  if (routes.includes(pathname as RoutePath)) return pathname as RoutePath;
  return "/";
}

function HealthCheckPage() {
  const [health, setHealth] = useState<HealthCheckResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);

  async function checkBackend() {
    setChecking(true);
    setError(null);

    try {
      setHealth(await verifyApiConnection());
    } catch (cause) {
      setHealth(null);
      setError(cause instanceof Error ? cause.message : "Unknown error");
    } finally {
      setChecking(false);
    }
  }

  return (
    <main className="shell">
      <section className="card" aria-labelledby="title">
        <p className="eyebrow">TraVerse frontend foundation</p>
        <h1 id="title">Frontend foundation is ready.</h1>
        <p className="description">
          The React frontend is connected to the application architecture. Verify
          the real Django health boundary before building application features.
        </p>

        <button type="button" onClick={checkBackend} disabled={checking}>
          {checking ? "Checking backend…" : "Check backend health"}
        </button>

        {health && (
          <div className="result success" role="status">
            <strong>Backend healthy</strong>
            <span>Database: {health.services.database}</span>
            <span>Redis: {health.services.redis}</span>
            <span>Django: {health.services.django}</span>
          </div>
        )}

        {error && (
          <div className="result error" role="alert">
            <strong>Backend verification failed</strong>
            <span>{error}</span>
          </div>
        )}
      </section>
    </main>
  );
}

function PlaceholderPage({ path }: { path: Exclude<RoutePath, "/"> }) {
  const labels: Record<Exclude<RoutePath, "/">, string> = {
    "/login": "Login",
    "/register": "Register",
    "/destinations": "Destinations",
    "/trips": "Trips",
  };

  return (
    <main className="shell">
      <section className="card" aria-labelledby="title">
        <p className="eyebrow">TraVerse</p>
        <h1 id="title">{labels[path]}</h1>
        <p className="description">
          This route is registered in the frontend architecture and is ready for
          its feature implementation.
        </p>
      </section>
    </main>
  );
}

function RouteView({ path }: { path: RoutePath }) {
  if (path === "/") return <HealthCheckPage />;
  return <PlaceholderPage path={path} />;
}

export function Router() {
  const [path, setPath] = useState<RoutePath>(() => normalizePath(window.location.pathname));

  useEffect(() => {
    const onPopState = () => setPath(normalizePath(window.location.pathname));
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  return <RouteView path={path} />;
}
