import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as itineraryApi from "../api/itineraryApi";
import { useTripItinerary } from "../hooks/useTripItinerary";

function createWrapper() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: ReactNode }) => <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useTripItinerary", () => {
  afterEach(() => vi.restoreAllMocks());

  it("does not request itinerary data without a trip id", () => {
    const fetchSpy = vi.spyOn(itineraryApi, "fetchTripItinerary").mockResolvedValue([]);

    const { result } = renderHook(() => useTripItinerary(""), { wrapper: createWrapper() });

    expect(result.current.fetchStatus).toBe("idle");
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("fetches itinerary data for a trip id", async () => {
    vi.spyOn(itineraryApi, "fetchTripItinerary").mockResolvedValue([{ id: "day-1", date: "2026-09-01", day_number: 1, summary: "", items: [] }]);

    const { result } = renderHook(() => useTripItinerary("trip-1"), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data?.[0].id).toBe("day-1"));
  });
});
