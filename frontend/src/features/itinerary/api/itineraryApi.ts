import { apiRequest } from "../../../lib/apiClient";
import type { Destination } from "../../destinations/api/destinationsApi";

export interface ItineraryItem {
  id: string;
  order: number;
  title: string;
  description: string;
  start_time: string | null;
  estimated_cost_usd: string | null;
  is_ai_generated: boolean;
  destination: Destination | null;
}

export interface ItineraryDay {
  id: string;
  date: string;
  day_number: number;
  summary: string;
  items: ItineraryItem[];
}

export interface AddItineraryItemPayload {
  title: string;
  description?: string;
  start_time?: string | null;
  estimated_cost_usd?: string | null;
  destination_id?: string | null;
}

interface AddItineraryItemResponse {
  id: string;
  message: string;
}

export function fetchTripItinerary(tripId: string): Promise<ItineraryDay[]> {
  return apiRequest<ItineraryDay[]>(`/api/itinerary/trips/${tripId}/itinerary/`);
}

export function addItineraryItem(dayId: string, payload: AddItineraryItemPayload): Promise<AddItineraryItemResponse> {
  return apiRequest<AddItineraryItemResponse>(`/api/itinerary/itinerary-days/${dayId}/items/`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
