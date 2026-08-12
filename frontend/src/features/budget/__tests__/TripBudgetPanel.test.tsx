import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TripBudgetPanel } from "../components/TripBudgetPanel";

const mutate = vi.fn();

let budgetState = {
  data: {
    id: "budget-1",
    currency: "USD",
    planned_total: null,
    computed_total: "40.00",
    line_items: [
      {
        id: "item-1",
        category: "food" as const,
        description: "Lunch",
        amount: "15.00",
        is_ai_estimated: false,
        created_at: "2026-09-01T00:00:00Z",
      },
    ],
  },
  isLoading: false,
  isError: false,
  error: null as Error | null,
  refetch: vi.fn(),
};

vi.mock("../hooks/useTripBudget", () => ({
  useTripBudget: () => budgetState,
}));

vi.mock("../hooks/useCreateBudgetLineItem", () => ({
  useCreateBudgetLineItem: () => ({
    mutate,
    isPending: false,
    isError: false,
    error: null,
  }),
}));

describe("TripBudgetPanel", () => {
  beforeEach(() => {
    mutate.mockClear();
    budgetState = {
      data: {
        id: "budget-1",
        currency: "USD",
        planned_total: null,
        computed_total: "40.00",
        line_items: [
          {
            id: "item-1",
            category: "food",
            description: "Lunch",
            amount: "15.00",
            is_ai_estimated: false,
            created_at: "2026-09-01T00:00:00Z",
          },
        ],
      },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    };
  });

  it("renders budget totals and line items", () => {
    render(<TripBudgetPanel tripId="trip-1" />);

    expect(
      screen.getByRole("heading", { name: "Cost planning" }),
    ).toBeInTheDocument();
    expect(screen.getByText("$40.00")).toBeInTheDocument();
    expect(screen.getByText("Lunch")).toBeInTheDocument();
  });

  it("validates the description locally", () => {
    render(<TripBudgetPanel tripId="trip-1" />);

    fireEvent.change(screen.getByLabelText("Amount"), {
      target: { value: "25" },
    });
    fireEvent.submit(
      screen.getByRole("button", { name: "Add budget item" }).closest("form")!,
    );

    expect(screen.getByText("Description is required.")).toBeInTheDocument();
    expect(mutate).not.toHaveBeenCalled();
  });

  it("submits a backend-compatible add line item mutation", () => {
    render(<TripBudgetPanel tripId="trip-1" />);

    fireEvent.change(screen.getByLabelText("Category"), {
      target: { value: "transport" },
    });
    fireEvent.change(screen.getByLabelText("Description"), {
      target: { value: "Metro" },
    });
    fireEvent.change(screen.getByLabelText("Amount"), {
      target: { value: "12.50" },
    });
    fireEvent.submit(
      screen.getByRole("button", { name: "Add budget item" }).closest("form")!,
    );

    expect(mutate).toHaveBeenCalledWith(
      {
        tripId: "trip-1",
        payload: {
          category: "transport",
          description: "Metro",
          amount: "12.50",
        },
      },
      expect.objectContaining({ onSuccess: expect.any(Function) }),
    );
  });

  it("renders an empty state when no line items exist", () => {
    budgetState = {
      ...budgetState,
      data: {
        ...budgetState.data,
        computed_total: "0.00",
        line_items: [],
      },
    };

    render(<TripBudgetPanel tripId="trip-1" />);

    expect(
      screen.getByText(/No budget line items yet/),
    ).toBeInTheDocument();
  });
});
