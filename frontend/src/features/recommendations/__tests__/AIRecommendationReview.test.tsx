import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { Recommendation } from "../api/recommendationsApi";
import { AIRecommendationReview } from "../components/AIRecommendationReview";

function recommendation(overrides: Partial<Recommendation>): Recommendation {
  return {
    id: "recommendation-1",
    category: "attraction",
    score: "0.70",
    reason: "A strong cultural fit for this trip.",
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
    ...overrides,
  };
}

describe("AIRecommendationReview", () => {
  it("orders AI recommendations by backend score", () => {
    render(
      <AIRecommendationReview
        recommendations={[
          recommendation({ id: "low", score: "0.62", destination: { ...recommendation({}).destination, id: "low-destination", name: "Low score place" } }),
          recommendation({ id: "high", score: "0.94", destination: { ...recommendation({}).destination, id: "high-destination", name: "High score place" } }),
        ]}
        onAccept={vi.fn()}
        onReject={vi.fn()}
        acceptPending={false}
        rejectPending={false}
      />,
    );

    const names = screen.getAllByRole("heading", { level: 4 }).map((element) => element.textContent);
    expect(names).toEqual(["High score place", "Low score place"]);
    expect(screen.getByText("94% match")).toBeInTheDocument();
  });

  it("shows decision controls only for pending recommendations", () => {
    render(
      <AIRecommendationReview
        recommendations={[
          recommendation({ id: "pending", status: "pending", destination: { ...recommendation({}).destination, name: "Pending place" } }),
          recommendation({ id: "accepted", status: "accepted", destination: { ...recommendation({}).destination, id: "accepted-destination", name: "Accepted place" } }),
        ]}
        onAccept={vi.fn()}
        onReject={vi.fn()}
        acceptPending={false}
        rejectPending={false}
      />,
    );

    expect(screen.getByRole("button", { name: "Keep recommendation" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Dismiss" })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Keep recommendation" })).toHaveLength(1);
  });

  it("calls the supplied accept and reject handlers", () => {
    const onAccept = vi.fn();
    const onReject = vi.fn();

    render(
      <AIRecommendationReview
        recommendations={[recommendation({ id: "recommendation-42" })]}
        onAccept={onAccept}
        onReject={onReject}
        acceptPending={false}
        rejectPending={false}
      />,
    );

    screen.getByRole("button", { name: "Keep recommendation" }).click();
    screen.getByRole("button", { name: "Dismiss" }).click();

    expect(onAccept).toHaveBeenCalledWith("recommendation-42");
    expect(onReject).toHaveBeenCalledWith("recommendation-42");
  });
});
