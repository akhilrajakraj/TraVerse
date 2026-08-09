import { useState } from "react";

import { verifyApiConnection } from "./lib/verifyApiConnection";
import type { HealthCheckResult } from "./types/health";

export default function App() {
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
          Chapter 1 is intentionally small: verify the React toolchain and the
          real Django health boundary before building application features.
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
