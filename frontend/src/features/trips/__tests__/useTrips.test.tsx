import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useTrips } from "../hooks/useTrips";
import * as tripsApi from "../api/tripsApi";

function createWrapper() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
}

describe("useTrips", () => {
  afterEach(() => vi.restoreAllMocks());

  it("returns the shared list shape for the current trip response", async () => {
    const trips = [
      {
        id: "trip-1",
        title: "Japan",
        start_date: "2026-09-01",
        end_date: "2026-09-05",
        duration_days: 5,
        status: "draft",
        traveler_count: 1,
        notes: "",
        computed_budget_total: null,
        destinations: [],
        created_at: "",
        updated_at: "",
      },
    ];

    vi.spyOn(tripsApi, "fetchTrips").mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: trips,
    });

    const { result } = renderHook(() => useTrips(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.results[0].title).toBe("Japan");
    expect(result.current.data?.count).toBe(1);
  });
});
