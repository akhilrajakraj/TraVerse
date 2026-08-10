import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatusBadge } from "../StatusBadge";
import { agentRunStatusColors, tripStatusColors } from "../../../lib/statusColors";

describe("StatusBadge", () => {
  it("renders the raw status text by default", () => {
    render(<StatusBadge status="succeeded" colorMap={agentRunStatusColors} />);
    expect(screen.getByText("succeeded")).toBeInTheDocument();
  });

  it("renders a custom label when provided", () => {
    render(<StatusBadge status="succeeded" colorMap={agentRunStatusColors} label="Complete" />);
    expect(screen.getByText("Complete")).toBeInTheDocument();
  });

  it("falls back to neutral for an unrecognized status without crashing", () => {
    render(<StatusBadge status="some_future_status" colorMap={tripStatusColors} />);
    expect(screen.getByText("some_future_status")).toBeInTheDocument();
  });
});
