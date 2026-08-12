import { afterEach, describe, expect, it, vi } from "vitest";

import { apiRequest } from "../../../lib/apiClient";
import {
  createBudgetLineItem,
  fetchTripBudget,
} from "../api/budgetApi";

vi.mock("../../../lib/apiClient", () => ({
  apiRequest: vi.fn(),
}));

describe("budgetApi", () => {
  afterEach(() => vi.mocked(apiRequest).mockReset());

  it("fetches a trip budget from the actual backend path", async () => {
    vi.mocked(apiRequest).mockResolvedValueOnce({
      id: "budget-1",
      currency: "USD",
      planned_total: null,
      computed_total: "0.00",
      line_items: [],
    });

    await fetchTripBudget("trip-123");

    expect(apiRequest).toHaveBeenCalledWith(
      "/api/budget/trips/trip-123/budget/",
    );
  });

  it("posts a backend-compatible budget line item payload", async () => {
    vi.mocked(apiRequest).mockResolvedValueOnce({
      id: "item-1",
      category: "food",
      description: "Lunch",
      amount: "15.00",
      is_ai_estimated: false,
      created_at: "2026-09-01T00:00:00Z",
    });

    await createBudgetLineItem("trip-123", {
      category: "food",
      description: "Lunch",
      amount: "15.00",
    });

    expect(apiRequest).toHaveBeenCalledWith(
      "/api/budget/trips/trip-123/budget/items/",
      {
        method: "POST",
        body: JSON.stringify({
          category: "food",
          description: "Lunch",
          amount: "15.00",
        }),
      },
    );
  });
});
