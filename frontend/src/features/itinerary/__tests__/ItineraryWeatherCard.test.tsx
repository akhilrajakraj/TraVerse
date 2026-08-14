import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { ItineraryDay } from "../api/itineraryApi";
import { ItineraryWeatherCard } from "../components/ItineraryWeatherCard";

const day: ItineraryDay = {
  id: "day-1",
  date: "2026-09-01",
  day_number: 1,
  summary: "Arrival day",
  weather_condition: "Partly cloudy",
  weather_high_f: 82,
  weather_low_f: 68,
  weather_precipitation_chance: 30,
  items: [],
};

describe("ItineraryWeatherCard", () => {
  it("renders the backend weather fields for a populated day", () => {
    render(<ItineraryWeatherCard day={day} />);

    expect(screen.getByText("Partly cloudy")).toBeInTheDocument();
    expect(screen.getByText("82°F")).toBeInTheDocument();
    expect(screen.getByText("68°F")).toBeInTheDocument();
    expect(screen.getByText("30%")).toBeInTheDocument();
  });

  it("renders a graceful missing-weather state when no weather is available", () => {
    render(
      <ItineraryWeatherCard
        day={{
          ...day,
          weather_condition: "",
          weather_high_f: null,
          weather_low_f: null,
          weather_precipitation_chance: null,
        }}
      />,
    );

    expect(screen.getByText("Weather information is not available for this day yet.")).toBeInTheDocument();
  });

  it("renders partial weather data without inventing missing values", () => {
    render(
      <ItineraryWeatherCard
        day={{
          ...day,
          weather_condition: "Rain",
          weather_high_f: 70,
          weather_low_f: null,
          weather_precipitation_chance: null,
        }}
      />,
    );

    expect(screen.getByText("Rain")).toBeInTheDocument();
    expect(screen.getByText("70°F")).toBeInTheDocument();
    expect(screen.getAllByText("—")).toHaveLength(2);
  });
});
