import { apiRequest } from "../../../lib/apiClient";
import type { PaginatedResponse } from "../../../lib/types";

export interface Destination {
  id: string;
  name: string;
  country: string;
  city: string;
  latitude: string;
  longitude: string;
  image_url: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export function searchDestinations(searchTerm: string): Promise<PaginatedResponse<Destination>> {
  const params = new URLSearchParams();
  if (searchTerm.trim()) params.set("search", searchTerm.trim());

  const query = params.toString();
  return apiRequest<PaginatedResponse<Destination>>(
    `/api/destinations/${query ? `?${query}` : ""}`,
  );
}
