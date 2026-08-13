import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AgentRunStatusIndicator } from "../components/AgentRunStatusIndicator";

describe("AgentRunStatusIndicator", () => {
  it.each([
    ["pending", "Planning request accepted"],
    ["running", "AI planner is working"],
    ["succeeded", "Your AI trip plan is ready"],
    ["failed", "The AI planner could not complete the run"],
    ["needs_review", "The AI planner needs another attempt"],
  ] as const)("renders the backend-owned %s state", (status, title) => {
    render(<AgentRunStatusIndicator status={status} />);

    expect(screen.getByText(title)).toBeInTheDocument();
    expect(screen.getByLabelText(`AI planner status: ${status}`)).toBeInTheDocument();
  });

  it("shows the live progress treatment for a running Agent Run", () => {
    render(<AgentRunStatusIndicator status="running" />);

    expect(screen.getByRole("status")).toHaveTextContent(
      "Status is refreshed automatically while the Agent Run remains active.",
    );
    expect(screen.getByText("Processing")).toBeInTheDocument();
    expect(screen.getByText("Backend workflow is executing.")).toBeInTheDocument();
  });

  it("keeps a needs_review diagnostic secondary to the recovery message", () => {
    render(
      <AgentRunStatusIndicator
        status="needs_review"
        errorMessage="Structured output validation failed."
      />,
    );

    expect(screen.getByText("This run is not treated as a completed AI plan.")).toBeInTheDocument();
    expect(screen.getByText("Show technical diagnostic")).toBeInTheDocument();
    expect(screen.getByText("Structured output validation failed.")).toBeInTheDocument();
  });
});
