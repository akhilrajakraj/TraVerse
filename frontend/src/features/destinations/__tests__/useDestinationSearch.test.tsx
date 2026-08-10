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

describe("useDestinationSearch", () => {
  it("caches distinct search terms and reuses a previous term", async () => {
    const searchSpy = vi.spyOn(destinationsApi, "searchDestinations").mockImplementation((term) =>
      Promise.resolve({
        count: 1,
        next: null,
        previous: null,
        results: [{
          id: term,
          name: term,
          country: "X",
          city: "Y",
          latitude: "0",
          longitude: "0",
          image_url: "",
          is_active: true,
          created_at: "",
          updated_at: "",
        }],
      }),
    );

    const { result, rerender } = renderHook(({ term }) => useDestinationSearch(term), {
      wrapper: createWrapper(),
      initialProps: { term: "tokyo" },
    });

    await waitFor(() => expect(result.current.data?.results[0].name).toBe("tokyo"));
    rerender({ term: "paris" });
    await waitFor(() => expect(result.current.data?.results[0].name).toBe("paris"));
    rerender({ term: "tokyo" });
    await waitFor(() => expect(result.current.data?.results[0].name).toBe("tokyo"));

    expect(searchSpy).toHaveBeenCalledTimes(2);
    searchSpy.mockRestore();
  });
});
