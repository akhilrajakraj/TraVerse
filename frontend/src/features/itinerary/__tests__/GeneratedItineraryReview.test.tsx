import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { ItineraryDay } from "../api/itineraryApi";
import { GeneratedItineraryReview } from "../components/GeneratedItineraryReview";

const day: ItineraryDay = {
  id: "day-1",
  date: "2026-09-01",
  day_number: 1,
  summary: "Arrival day",
  items: [
    {
      id: "item-ai",
      order: 1,
      title: "Visit the museum",
      description: "Explore the main collection.",
      start_time: "10:30",
      estimated_cost_usd: "25.00",
      is_ai_generated: true,
      destination: null,
    },
    {
      id: "item-manual",
      order: 2,
      title: "Coffee break",
      description: "Find a nearby cafe.",
      start_time: "14:00",
      estimated_cost_usd: null,
      is_ai_generated: false,
      destination: null,
    },
  ],
};

describe("GeneratedItineraryReview", () => {
  it("distinguishes AI-generated and manually added itinerary items", () => {
    render(<GeneratedItineraryReview day={day} />);

    expect(screen.getByText("Visit the museum")).toBeInTheDocument();
    expect(screen.getByText("Coffee break")).toBeInTheDocument();
    expect(screen.getByText("AI-generated")).toBeInTheDocument();
    expect(screen.getByText("Added by you")).toBeInTheDocument();
  });

  it("renders an empty state for a day without activities", () => {
    render(
      <GeneratedItineraryReview
        day={{ ...day, items: [] }}
      />,
    );

    expect(screen.getByText("Day 1 does not have activities yet.")).toBeInTheDocument();
  });
});
