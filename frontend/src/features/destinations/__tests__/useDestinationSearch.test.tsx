import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { useDestinationSearch } from "../hooks/useDestinationSearch";
import * as destinationsApi from "../api/destinationsApi";

function createWrapper() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
}

const destinations = [
  {
    id: "tokyo",
    name: "Tokyo",
    country: "Japan",
    city: "Tokyo",
    latitude: "35.6762",
    longitude: "139.6503",
    image_url: "",
    is_active: true,
    created_at: "",
    updated_at: "",
  },
  {
    id: "paris",
    name: "Paris",
    country: "France",
    city: "Paris",
    latitude: "48.8566",
    longitude: "2.3522",
    image_url: "",
    is_active: true,
    created_at: "",
    updated_at: "",
  },
];

describe("useDestinationSearch", () => {
  it("filters the shared catalog without changing the backend request", async () => {
    const getDestinationsSpy = vi.spyOn(destinationsApi, "getDestinations").mockResolvedValue({
      count: destinations.length,
      next: null,
      previous: null,
      results: destinations,
    });

    const { result, rerender } = renderHook(({ term }) => useDestinationSearch(term), {
      wrapper: createWrapper(),
      initialProps: { term: "tokyo" },
    });

    await waitFor(() => expect(result.current.data?.results[0].name).toBe("Tokyo"));
    rerender({ term: "paris" });
    await waitFor(() => expect(result.current.data?.results[0].name).toBe("Paris"));
    rerender({ term: "tokyo" });
    await waitFor(() => expect(result.current.data?.results[0].name).toBe("Tokyo"));

    expect(getDestinationsSpy).toHaveBeenCalledTimes(1);
    getDestinationsSpy.mockRestore();
  });
});
