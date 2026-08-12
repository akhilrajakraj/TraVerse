import { describe, expect, it, vi, afterEach } from "vitest";

import { addItineraryItem, fetchTripItinerary } from "../api/itineraryApi";
import { apiRequest } from "../../../lib/apiClient";

vi.mock("../../../lib/apiClient", () => ({
  apiRequest: vi.fn(),
}));

describe("itineraryApi", () => {
  afterEach(() => vi.mocked(apiRequest).mockReset());

  it("fetches a trip itinerary from the actual backend path", async () => {
    vi.mocked(apiRequest).mockResolvedValueOnce([]);

    await fetchTripItinerary("trip-123");

    expect(apiRequest).toHaveBeenCalledWith("/api/itinerary/trips/trip-123/itinerary/");
  });

  it("posts a backend-compatible add-item payload", async () => {
    vi.mocked(apiRequest).mockResolvedValueOnce({ id: "item-1", message: "created" });

    await addItineraryItem("day-123", { title: "Museum", start_time: "10:30", estimated_cost_usd: "24.50" });

    expect(apiRequest).toHaveBeenCalledWith("/api/itinerary/itinerary-days/day-123/items/", {
      method: "POST",
      body: JSON.stringify({ title: "Museum", start_time: "10:30", estimated_cost_usd: "24.50" }),
    });
  });
});
