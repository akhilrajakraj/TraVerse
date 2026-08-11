import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { DestinationsPage } from "../pages/DestinationsPage";
import * as destinationsApi from "../api/destinationsApi";

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <DestinationsPage />
    </QueryClientProvider>,
  );
}

describe("DestinationsPage", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("shows an empty state for zero search results", async () => {
    vi.spyOn(destinationsApi, "getDestinations").mockResolvedValue({
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          id: "destination-1",
          name: "Kyoto",
          country: "Japan",
          city: "Kyoto",
          latitude: "35.0116",
          longitude: "135.7681",
          image_url: "",
          is_active: true,
          created_at: "",
          updated_at: "",
        },
        {
          id: "destination-2",
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
      ],
    });

    renderPage();
    fireEvent.change(screen.getByRole("textbox", { name: "Search destinations" }), {
      target: { value: "unknown" },
    });

    await vi.runAllTimersAsync();
    expect(screen.getByText("No destinations found. Try a different search term.")).toBeInTheDocument();
  });

  it("renders destination cards for search results", async () => {
    vi.spyOn(destinationsApi, "getDestinations").mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [{
        id: "destination-1",
        name: "Kyoto",
        country: "Japan",
        city: "Kyoto",
        latitude: "35.0116",
        longitude: "135.7681",
        image_url: "",
        is_active: true,
        created_at: "",
        updated_at: "",
      }],
    });

    renderPage();
    fireEvent.change(screen.getByRole("textbox", { name: "Search destinations" }), {
      target: { value: "kyoto" },
    });

    await vi.runAllTimersAsync();
    expect(screen.getByText("Kyoto")).toBeInTheDocument();
    expect(screen.getByText("Kyoto, Japan")).toBeInTheDocument();
  });
});
