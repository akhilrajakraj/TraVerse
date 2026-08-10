import type { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ProfilePage } from "../pages/ProfilePage";
import * as profileApi from "../api/profileApi";

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}><ProfilePage /></QueryClientProvider>);
}

const profile = {
  id: "profile-1",
  user: "user-1",
  phone_number: "9876543210",
  date_of_birth: "2000-01-01",
  gender: "male" as const,
  profile_picture: "",
  bio: "Travel enthusiast",
  emergency_contact: { name: "Jane", phone: "9999999999" },
  created_at: "",
  updated_at: "",
};

describe("ProfilePage", () => {
  it("pre-fills editable profile data", async () => {
    vi.spyOn(profileApi, "fetchProfile").mockResolvedValue(profile);

    renderPage();

    await waitFor(() => expect(screen.getByDisplayValue("9876543210")).toBeInTheDocument());
    expect(screen.getByDisplayValue("Travel enthusiast")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Jane")).toBeInTheDocument();
  });

  it("submits profile changes through the feature API", async () => {
    vi.spyOn(profileApi, "fetchProfile").mockResolvedValue(profile);
    const updateSpy = vi.spyOn(profileApi, "updateProfile").mockResolvedValue({ ...profile, bio: "Updated traveler" });

    renderPage();
    await waitFor(() => screen.getByDisplayValue("Travel enthusiast"));

    fireEvent.change(screen.getByDisplayValue("Travel enthusiast"), { target: { value: "Updated traveler" } });
    fireEvent.click(screen.getByRole("button", { name: "Save profile" }));

    await waitFor(() => expect(updateSpy).toHaveBeenCalledWith(expect.objectContaining({ bio: "Updated traveler" })));
  });
});
