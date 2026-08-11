import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateProfile, type ProfileUpdatePayload } from "../api/profileApi";
import { PROFILE_QUERY_KEY } from "./useProfile";

export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: ProfileUpdatePayload) => updateProfile(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PROFILE_QUERY_KEY });
    },
  });
}
