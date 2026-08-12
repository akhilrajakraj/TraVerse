import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TripRecommendationsPanel } from "../components/TripRecommendationsPanel";

const acceptMutate = vi.fn();
const rejectMutate = vi.fn();

let recommendationState = {
  data: {
    count: 2,
    next: null,
    previous: null,
    results: [
      {
        id: "recommendation-1",
        category: "attraction" as const,
        score: "0.95",
        reason: "Excellent cultural experience.",
        status: "pending" as const,
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
      {
        id: "recommendation-2",
        category: "restaurant" as const,
        score: "0.82",
        reason: "Highly rated local cuisine.",
        status: "accepted" as const,
        is_ai_generated: true,
        destination: {
          id: "destination-2",
          name: "Gion Restaurant",
          country: "Japan",
          city: "Kyoto",
          latitude: "35.003700",
          longitude: "135.778800",
          image_url: "",
          is_active: true,
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
        },
        created_at: "2026-01-01T00:00:00Z",
      },
    ],
  },
  isLoading: false,
  isError: false,
  error: null as Error | null,
  refetch: vi.fn(),
};

vi.mock("../hooks/useTripRecommendations", () => ({
  useTripRecommendations: () => recommendationState,
}));

vi.mock("../hooks/useAcceptRecommendation", () => ({
  useAcceptRecommendation: () => ({
    mutate: acceptMutate,
    isPending: false,
    isError: false,
    error: null,
    variables: undefined,
  }),
}));

vi.mock("../hooks/useRejectRecommendation", () => ({
  useRejectRecommendation: () => ({
    mutate: rejectMutate,
    isPending: false,
    isError: false,
    error: null,
    variables: undefined,
  }),
}));

describe("TripRecommendationsPanel", () => {
  beforeEach(() => {
    acceptMutate.mockClear();
    rejectMutate.mockClear();
    recommendationState = {
      ...recommendationState,
      data: {
        ...recommendationState.data,
        results: [...recommendationState.data.results],
      },
    };
  });

  it("renders recommendation details and decision controls", () => {
    render(<TripRecommendationsPanel tripId="trip-1" />);

    expect(
      screen.getByRole("heading", { name: "Places worth considering" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Kyoto")).toBeInTheDocument();
    expect(screen.getByText("95% match")).toBeInTheDocument();
    expect(screen.getByText("Excellent cultural experience.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Keep recommendation" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Dismiss" })).toBeInTheDocument();
  });

  it("filters recommendations by lifecycle status", () => {
    render(<TripRecommendationsPanel tripId="trip-1" />);

    fireEvent.click(screen.getByRole("button", { name: "Accepted (1)" }));

    expect(screen.getByText("Gion Restaurant")).toBeInTheDocument();
    expect(screen.queryByText("Excellent cultural experience.")).not.toBeInTheDocument();
  });

  it("submits an accept decision for the selected recommendation", () => {
    render(<TripRecommendationsPanel tripId="trip-1" />);

    fireEvent.click(screen.getByRole("button", { name: "Keep recommendation" }));

    expect(acceptMutate).toHaveBeenCalledWith({
      recommendationId: "recommendation-1",
      tripId: "trip-1",
    });
  });

  it("submits a reject decision for the selected recommendation", () => {
    render(<TripRecommendationsPanel tripId="trip-1" />);

    fireEvent.click(screen.getByRole("button", { name: "Dismiss" }));

    expect(rejectMutate).toHaveBeenCalledWith({
      recommendationId: "recommendation-1",
      tripId: "trip-1",
    });
  });

  it("does not show decision controls for terminal recommendations", () => {
    recommendationState = {
      ...recommendationState,
      data: {
        ...recommendationState.data,
        count: 1,
        results: [recommendationState.data.results[1]],
      },
    };

    render(<TripRecommendationsPanel tripId="trip-1" />);

    expect(screen.getByText("Gion Restaurant")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Keep recommendation" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Dismiss" })).not.toBeInTheDocument();
  });
});
