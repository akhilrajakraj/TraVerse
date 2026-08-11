import { beforeEach, describe, expect, it, vi } from "vitest";

describe("apiClient refresh deduplication", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.resetModules();
  });

  it("shares one refresh request across concurrent 401 responses", async () => {
    localStorage.setItem("access_token", "expired");
    localStorage.setItem("refresh_token", "refresh");
    let refreshCalls = 0;
    const originalFetch = globalThis.fetch;

    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/token/refresh/")) {
        refreshCalls += 1;
        await new Promise((resolve) => setTimeout(resolve, 5));
        return new Response(JSON.stringify({ access: "fresh", refresh: "refresh-2" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }

      const headers = new Headers(init?.headers);
      if (headers.get("Authorization") === "Bearer fresh") {
        return new Response(JSON.stringify({ ok: true }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }

      return new Response(JSON.stringify({ detail: "expired" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      });
    }));

    try {
      const { apiRequest } = await import("../apiClient");
      const [first, second] = await Promise.all([
        apiRequest<{ ok: boolean }>("/api/a"),
        apiRequest<{ ok: boolean }>("/api/b"),
      ]);

      expect(first.ok).toBe(true);
      expect(second.ok).toBe(true);
      expect(refreshCalls).toBe(1);
      expect(localStorage.getItem("access_token")).toBe("fresh");
      expect(localStorage.getItem("refresh_token")).toBe("refresh-2");
    } finally {
      vi.stubGlobal("fetch", originalFetch);
    }
  });
});
