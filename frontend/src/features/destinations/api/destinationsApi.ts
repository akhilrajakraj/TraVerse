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

type DestinationApiResponse = Destination[] | PaginatedResponse<Destination>;

/**
 * The backend destination endpoint currently returns the active catalog as a
 * plain JSON array. Normalize that response at the API boundary so the rest of
 * the feature can keep using the shared paginated list shape.
 *
 * Supporting the paginated envelope as well keeps this frontend compatible if
 * the backend endpoint adopts pagination later without changing the page or
 * search hook.
 */
export async function getDestinations(): Promise<PaginatedResponse<Destination>> {
  const response = await apiRequest<DestinationApiResponse>("/api/destinations/");

  if (Array.isArray(response)) {
    return {
      count: response.length,
      next: null,
      previous: null,
      results: response,
    };
  }

  return response;
}
