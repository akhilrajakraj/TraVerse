import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { CreateTripPage } from "../pages/CreateTripPage";

const mutate = vi.fn();

vi.mock("../hooks/useCreateTrip", () => ({
  useCreateTrip: () => ({
    mutate,
    isPending: false,
    isError: false,
  }),
}));

vi.mock("../../destinations/hooks/useDestinationSearch", () => ({
  useDestinationSearch: () => ({
    data: { count: 0, next: null, previous: null, results: [] },
    isLoading: false,
    isError: false,
  }),
}));

describe("CreateTripPage", () => {
  it("submits the backend-compatible trip payload without a status field", () => {
    render(<CreateTripPage />);

    fireEvent.change(screen.getByRole("textbox", { name: "Trip title" }), {
      target: { value: "Japan Adventure" },
    });
    fireEvent.change(screen.getByLabelText("Start date"), {
      target: { value: "2026-09-01" },
    });
    fireEvent.change(screen.getByLabelText("End date"), {
      target: { value: "2026-09-05" },
    });
    fireEvent.change(screen.getByLabelText("Travelers"), {
      target: { value: "2" },
    });
    fireEvent.change(screen.getByLabelText(/Notes/), {
      target: { value: "Rail pass" },
    });

    fireEvent.submit(screen.getByRole("button", { name: "Create trip" }).closest("form")!);

    expect(mutate).toHaveBeenCalledWith({
      title: "Japan Adventure",
      start_date: "2026-09-01",
      end_date: "2026-09-05",
      destination_ids: [],
      traveler_count: 2,
      notes: "Rail pass",
    });
    expect(mutate.mock.calls[0][0]).not.toHaveProperty("status");
  });

  it("rejects an end date before the start date locally", () => {
    render(<CreateTripPage />);

    fireEvent.change(screen.getByRole("textbox", { name: "Trip title" }), {
      target: { value: "Invalid Trip" },
    });
    fireEvent.change(screen.getByLabelText("Start date"), {
      target: { value: "2026-09-05" },
    });
    fireEvent.change(screen.getByLabelText("End date"), {
      target: { value: "2026-09-01" },
    });
    fireEvent.submit(screen.getByRole("button", { name: "Create trip" }).closest("form")!);

    expect(screen.getByText("The end date must be on or after the start date.")).toBeInTheDocument();
    expect(mutate).not.toHaveBeenCalled();
  });
});
