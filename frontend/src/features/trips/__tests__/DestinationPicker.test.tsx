import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { Destination } from "../../destinations/api/destinationsApi";
import { DestinationPicker } from "../components/DestinationPicker";

const destinations: Destination[] = [
  {
    id: "destination-1",
    name: "Kyoto",
    country: "Japan",
    city: "Kyoto",
    latitude: "35.0116",
    longitude: "135.7681",
    image_url: "",
    is_active: true,
    created_at: "",
    updated_at: "",
  },
];

vi.mock("../../destinations/hooks/useDestinationSearch", () => ({
  useDestinationSearch: (searchTerm: string) => ({
    data: searchTerm
      ? { count: destinations.length, next: null, previous: null, results: destinations }
      : { count: destinations.length, next: null, previous: null, results: destinations },
    isLoading: false,
    isError: false,
  }),
}));

describe("DestinationPicker", () => {
  it("adds a destination and clears the search term", () => {
    const onChange = vi.fn();
    render(<DestinationPicker selected={[]} onChange={onChange} />);

    const input = screen.getByRole("textbox", { name: "Search destinations to add" });
    fireEvent.change(input, { target: { value: "kyo" } });
    fireEvent.click(screen.getByRole("button", { name: /Kyoto, Japan/ }));

    expect(onChange).toHaveBeenCalledWith([destinations[0]]);
    expect(input).toHaveValue("");
  });

  it("does not add the same destination twice", () => {
    const onChange = vi.fn();
    render(<DestinationPicker selected={destinations} onChange={onChange} />);

    const input = screen.getByRole("textbox", { name: "Search destinations to add" });
    fireEvent.change(input, { target: { value: "kyo" } });

    expect(screen.queryByRole("button", { name: /Kyoto, Japan/ })).not.toBeInTheDocument();
  });
});
