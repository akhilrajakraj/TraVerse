import type { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useProfile } from "../hooks/useProfile";
import * as profileApi from "../api/profileApi";

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useProfile", () => {
  it("loads the authenticated user's profile", async () => {
    vi.spyOn(profileApi, "fetchProfile").mockResolvedValue({
      id: "profile-1",
      user: "user-1",
      phone_number: "9876543210",
      date_of_birth: null,
      gender: "prefer_not_to_say",
      profile_picture: "",
      bio: "Traveler",
      emergency_contact: {},
      created_at: "",
      updated_at: "",
    });

    const { result } = renderHook(() => useProfile(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.phone_number).toBe("9876543210");
  });
});
