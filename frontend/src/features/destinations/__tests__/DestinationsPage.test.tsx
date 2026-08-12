import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

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

const destination = {
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
};

describe("DestinationsPage", () => {
  it("loads and renders the catalog without requiring a search term", async () => {
    const getDestinationsSpy = vi.spyOn(destinationsApi, "getDestinations").mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [destination],
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Kyoto")).toBeInTheDocument();
      expect(screen.getByText("Kyoto, Japan")).toBeInTheDocument();
    });

    expect(getDestinationsSpy).toHaveBeenCalledTimes(1);
    getDestinationsSpy.mockRestore();
  });

  it("shows an empty state for zero search results", async () => {
    vi.spyOn(destinationsApi, "getDestinations").mockResolvedValue({
      count: 2,
      next: null,
      previous: null,
      results: [
        destination,
        {
          ...destination,
          id: "destination-2",
          name: "Paris",
          country: "France",
          city: "Paris",
        },
      ],
    });

    renderPage();
    fireEvent.change(screen.getByRole("textbox", { name: "Search destinations" }), {
      target: { value: "unknown" },
    });

    await waitFor(() => {
      expect(screen.getByText("No destinations found. Try a different search term.")).toBeInTheDocument();
    }, { timeout: 2000 });
  });

  it("renders destination cards for search results", async () => {
    vi.spyOn(destinationsApi, "getDestinations").mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [destination],
    });

    renderPage();
    fireEvent.change(screen.getByRole("textbox", { name: "Search destinations" }), {
      target: { value: "kyoto" },
    });

    await waitFor(() => {
      expect(screen.getByText("Kyoto")).toBeInTheDocument();
      expect(screen.getByText("Kyoto, Japan")).toBeInTheDocument();
    }, { timeout: 2000 });
  });
});
