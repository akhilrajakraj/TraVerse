import { useQuery } from "@tanstack/react-query";
import { fetchProfile } from "../api/profileApi";

export const PROFILE_QUERY_KEY = ["profile", "me"] as const;

export function useProfile() {
  return useQuery({
    queryKey: PROFILE_QUERY_KEY,
    queryFn: fetchProfile,
  });
}
