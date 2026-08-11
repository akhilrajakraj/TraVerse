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

/**
 * The backend destination endpoint exposes the active catalog. Search is
 * intentionally kept client-side so the frontend does not change the
 * established backend API contract.
 */
export function getDestinations(): Promise<PaginatedResponse<Destination>> {
  return apiRequest<PaginatedResponse<Destination>>("/api/destinations/");
}
