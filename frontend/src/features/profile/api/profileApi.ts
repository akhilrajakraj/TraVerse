import { apiRequest } from "../../../lib/apiClient";

export interface UserProfile {
  id: string;
  user: string;
  phone_number: string;
  date_of_birth: string | null;
  gender: "male" | "female" | "other" | "prefer_not_to_say" | "";
  profile_picture: string;
  bio: string;
  emergency_contact: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export type ProfileUpdatePayload = Partial<
  Pick<
    UserProfile,
    | "phone_number"
    | "date_of_birth"
    | "gender"
    | "profile_picture"
    | "bio"
    | "emergency_contact"
  >
>;

export function fetchProfile(): Promise<UserProfile> {
  return apiRequest<UserProfile>("/api/profiles/me/");
}

export function updateProfile(payload: ProfileUpdatePayload): Promise<UserProfile> {
  return apiRequest<UserProfile>("/api/profiles/me/", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
