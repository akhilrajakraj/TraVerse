import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useTrip } from "../hooks/useTrip";
import * as tripsApi from "../api/tripsApi";

function createWrapper() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
}

describe("useTrip", () => {
  afterEach(() => vi.restoreAllMocks());

  it("does not request a trip when no id is available", () => {
    const fetchTripSpy = vi.spyOn(tripsApi, "fetchTrip").mockResolvedValue({
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
    });

    const { result } = renderHook(() => useTrip(""), { wrapper: createWrapper() });

    expect(result.current.fetchStatus).toBe("idle");
    expect(fetchTripSpy).not.toHaveBeenCalled();
  });

  it("fetches a trip by its id", async () => {
    vi.spyOn(tripsApi, "fetchTrip").mockResolvedValue({
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
    });

    const { result } = renderHook(() => useTrip("trip-1"), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data?.id).toBe("trip-1"));
  });
});
