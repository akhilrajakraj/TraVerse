import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { HomePage } from "../pages/HomePage";

vi.mock("../../../lib/verifyApiConnection", () => ({
  verifyApiConnection: vi.fn().mockResolvedValue({ status: "healthy", services: { database: "healthy", redis: "healthy", django: "healthy" } }),
}));

describe("HomePage", () => {
  it("renders the primary travel planning experience", async () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    expect(screen.getByRole("heading", { name: /go somewhere/i })).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/search destinations/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /plan a trip/i })).toBeInTheDocument();
  });
});
