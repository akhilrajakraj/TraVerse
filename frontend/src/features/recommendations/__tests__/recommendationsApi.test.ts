import { afterEach, describe, expect, it, vi } from "vitest";

import { apiRequest } from "../../../lib/apiClient";
import {
  acceptRecommendation,
  fetchTripRecommendations,
  rejectRecommendation,
} from "../api/recommendationsApi";

vi.mock("../../../lib/apiClient", () => ({
  apiRequest: vi.fn(),
}));

describe("recommendationsApi", () => {
  afterEach(() => vi.mocked(apiRequest).mockReset());

  it("fetches recommendations from the current backend path and normalizes arrays", async () => {
    vi.mocked(apiRequest).mockResolvedValueOnce([
      {
        id: "recommendation-1",
        category: "attraction",
        score: "0.95",
        reason: "Great cultural experience.",
        status: "pending",
        is_ai_generated: true,
        destination: {
          id: "destination-1",
          name: "Kyoto",
          country: "Japan",
          city: "Kyoto",
          latitude: "35.011600",
          longitude: "135.768100",
          image_url: "",
          is_active: true,
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
        },
        created_at: "2026-01-01T00:00:00Z",
      },
    ]);

    const response = await fetchTripRecommendations("trip-123");

    expect(apiRequest).toHaveBeenCalledWith(
      "/api/recommendations/trips/trip-123/recommendations/",
    );
    expect(response.count).toBe(1);
    expect(response.results[0]?.destination.name).toBe("Kyoto");
  });

  it("accepts a recommendation through the existing endpoint", async () => {
    vi.mocked(apiRequest).mockResolvedValueOnce({ id: "recommendation-1" });

    await acceptRecommendation("recommendation-1");

    expect(apiRequest).toHaveBeenCalledWith(
      "/api/recommendations/recommendations/recommendation-1/accept/",
      { method: "POST" },
    );
  });

  it("rejects a recommendation through the existing endpoint", async () => {
    vi.mocked(apiRequest).mockResolvedValueOnce({ id: "recommendation-1" });

    await rejectRecommendation("recommendation-1");

    expect(apiRequest).toHaveBeenCalledWith(
      "/api/recommendations/recommendations/recommendation-1/reject/",
      { method: "POST" },
    );
  });
});
