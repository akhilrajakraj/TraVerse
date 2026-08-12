import { apiRequest } from "../../../lib/apiClient";
import type { PaginatedResponse } from "../../../lib/types";
import type { Destination } from "../../destinations/api/destinationsApi";

export interface Trip {
  id: string;
  title: string;
  start_date: string;
  end_date: string;
  duration_days: number;
  status: string;
  traveler_count: number;
  notes: string;
  computed_budget_total: string | null;
  destinations: Destination[];
  created_at: string;
  updated_at: string;
}

export interface CreateTripPayload {
  title: string;
  start_date: string;
  end_date: string;
  destination_ids: string[];
  traveler_count?: number;
  notes?: string;
}

type TripListResponse = Trip[] | PaginatedResponse<Trip>;

/**
 * The current backend returns the authenticated user's trip list as a plain
 * array because global DRF pagination is not enabled. Normalize that response
 * at the API boundary while also accepting a paginated envelope if pagination
 * is introduced later without requiring another frontend architecture change.
 */
export async function fetchTrips(): Promise<PaginatedResponse<Trip>> {
  const response = await apiRequest<TripListResponse>("/api/trips/");

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

export function fetchTrip(tripId: string): Promise<Trip> {
  return apiRequest<Trip>(`/api/trips/${tripId}/`);
}

export function createTrip(payload: CreateTripPayload): Promise<Trip> {
  return apiRequest<Trip>("/api/trips/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
