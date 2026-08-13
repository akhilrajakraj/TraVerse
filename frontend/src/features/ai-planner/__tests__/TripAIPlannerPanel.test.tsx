import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiRequestError } from "../../../lib/apiClient";
import { TripAIPlannerPanel } from "../components/TripAIPlannerPanel";

const mutate = vi.fn();
const invalidateQueries = vi.fn(() => Promise.resolve());

let statusState: any;
let triggerState: any;

vi.mock("@tanstack/react-query", () => ({ useQueryClient: () => ({ invalidateQueries }) }));
vi.mock("../hooks/useTripPlanStatus", () => ({ useTripPlanStatus: () => statusState }));
vi.mock("../hooks/useTriggerTripPlan", () => ({ useTriggerTripPlan: () => ({ ...triggerState, mutate }) }));

describe("TripAIPlannerPanel", () => {
  beforeEach(() => {
    mutate.mockClear();
    invalidateQueries.mockClear();
    statusState = {
      data: undefined,
      isLoading: false,
      isError: true,
      error: new ApiRequestError(404, "not_found", "No AI planning has been started for this trip."),
      refetch: vi.fn(),
    };
    triggerState = { isPending: false, isSuccess: false, isError: false, error: null };
  });

  it("renders the planner trigger when no AgentRun exists", () => {
    render(<TripAIPlannerPanel tripId="trip-1" />);
    expect(screen.getByRole("heading", { name: "Generate a trip plan" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Generate AI trip plan" })).toBeEnabled();
  });

  it("queues planning for the current trip", () => {
    render(<TripAIPlannerPanel tripId="trip-1" />);
    fireEvent.click(screen.getByRole("button", { name: "Generate AI trip plan" }));
    expect(mutate).toHaveBeenCalledWith("trip-1", expect.objectContaining({ onError: expect.any(Function) }));
  });

  it("makes needs_review actionable and keeps the parser diagnostic secondary", () => {
    statusState = {
      ...statusState,
      data: {
        id: "run-1",
        agent_type: "travel_planner",
        status: "needs_review",
        error_message: "Unable to produce valid structured output. Initial error: malformed JSON",
        started_at: "2026-09-01T10:00:00Z",
        completed_at: "2026-09-01T10:02:00Z",
      },
      isError: false,
      error: null,
    };
    render(<TripAIPlannerPanel tripId="trip-1" />);
    expect(screen.getByText("The AI planner needs another attempt")).toBeInTheDocument();
    expect(screen.getByText(/invalid structured data/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry AI planner" })).toBeEnabled();
    expect(screen.getByText(/No new AI-generated plan is considered complete/i)).toBeInTheDocument();
  });

  it("refreshes authoritative trip data after a successful planning run", () => {
    statusState = {
      ...statusState,
      data: {
        id: "run-1",
        agent_type: "travel_planner",
        status: "succeeded",
        error_message: "",
        started_at: "2026-09-01T10:00:00Z",
        completed_at: "2026-09-01T10:02:00Z",
      },
      isError: false,
      error: null,
    };
    render(<TripAIPlannerPanel tripId="trip-1" />);
    expect(screen.getByText("Your AI trip plan is ready")).toBeInTheDocument();
    expect(invalidateQueries).toHaveBeenCalledTimes(4);
  });
});
