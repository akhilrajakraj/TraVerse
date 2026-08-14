import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TripItineraryPanel } from "../components/TripItineraryPanel";

const mutate = vi.fn();
let itineraryState = {
  data: [{
    id: "day-1",
    date: "2026-09-01",
    day_number: 1,
    summary: "Arrival",
    weather_condition: "",
    weather_high_f: null,
    weather_low_f: null,
    weather_precipitation_chance: null,
    items: [],
  }],
  isLoading: false,
  isError: false,
  error: null as Error | null,
  refetch: vi.fn(),
};

vi.mock("../hooks/useTripItinerary", () => ({
  useTripItinerary: () => itineraryState,
}));

vi.mock("../hooks/useAddItineraryItem", () => ({
  useAddItineraryItem: () => ({ mutate, isPending: false, isError: false, error: null }),
}));

describe("TripItineraryPanel", () => {
  beforeEach(() => {
    mutate.mockClear();
    itineraryState = {
            data: [{ id: "day-1", date: "2026-09-01", day_number: 1, summary: "Arrival", weather_condition: "", weather_high_f: null, weather_low_f: null, weather_precipitation_chance: null, items: [] }],
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    };
  });

  it("renders the empty day state and add activity form", () => {
    render(<TripItineraryPanel tripId="trip-1" />);

    expect(screen.getByRole("heading", { name: "Day-by-day planner" })).toBeInTheDocument();
    expect(screen.getByText("Day 1 does not have activities yet.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add activity" })).toBeInTheDocument();
  });

  it("validates activity title locally", () => {
    render(<TripItineraryPanel tripId="trip-1" />);

    fireEvent.submit(screen.getByRole("button", { name: "Add activity" }).closest("form")!);

    expect(screen.getByText("Activity title is required.")).toBeInTheDocument();
    expect(mutate).not.toHaveBeenCalled();
  });

  it("submits a backend-compatible add item mutation", () => {
    render(<TripItineraryPanel tripId="trip-1" />);

    fireEvent.change(screen.getByRole("textbox", { name: "Activity title" }), { target: { value: "Museum" } });
    fireEvent.change(screen.getByLabelText("Description"), { target: { value: "Modern art" } });
    fireEvent.change(screen.getByLabelText("Start time"), { target: { value: "10:30" } });
    fireEvent.change(screen.getByLabelText("Estimated cost USD"), { target: { value: "25" } });
    fireEvent.submit(screen.getByRole("button", { name: "Add activity" }).closest("form")!);

    expect(mutate).toHaveBeenCalledWith({
      dayId: "day-1",
      tripId: "trip-1",
      payload: {
        title: "Museum",
        description: "Modern art",
        start_time: "10:30",
        estimated_cost_usd: "25",
      },
    }, expect.objectContaining({ onSuccess: expect.any(Function) }));
  });

  it("renders an itinerary-level empty state when no days exist", () => {
    itineraryState = { ...itineraryState, data: [] };

    render(<TripItineraryPanel tripId="trip-1" />);

    expect(screen.getByText(/No itinerary days exist for this trip yet/)).toBeInTheDocument();
  });
});
