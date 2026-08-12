import { apiRequest } from "../../../lib/apiClient";
import type { PaginatedResponse } from "../../../lib/types";

export type RecommendationCategory =
  | "restaurant"
  | "attraction"
  | "hotel"
  | "shopping"
  | "experience"
  | "hidden_gem";

export type RecommendationStatus = "pending" | "accepted" | "rejected";

export interface RecommendationDestination {
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

export interface Recommendation {
  id: string;
  category: RecommendationCategory;
  score: string;
  reason: string;
  status: RecommendationStatus;
  is_ai_generated: boolean;
  destination: RecommendationDestination;
  created_at: string;
}

type RecommendationListResponse = Recommendation[] | PaginatedResponse<Recommendation>;

function normalizeRecommendationList(
  response: RecommendationListResponse,
): PaginatedResponse<Recommendation> {
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

export async function fetchTripRecommendations(
  tripId: string,
): Promise<PaginatedResponse<Recommendation>> {
  const response = await apiRequest<RecommendationListResponse>(
    `/api/recommendations/trips/${tripId}/recommendations/`,
  );

  return normalizeRecommendationList(response);
}

export function acceptRecommendation(
  recommendationId: string,
): Promise<Recommendation> {
  return apiRequest<Recommendation>(
    `/api/recommendations/recommendations/${recommendationId}/accept/`,
    { method: "POST" },
  );
}

export function rejectRecommendation(
  recommendationId: string,
): Promise<Recommendation> {
  return apiRequest<Recommendation>(
    `/api/recommendations/recommendations/${recommendationId}/reject/`,
    { method: "POST" },
  );
}

export const recommendationCategoryLabels: Record<RecommendationCategory, string> = {
  restaurant: "Restaurant",
  attraction: "Attraction",
  hotel: "Hotel",
  shopping: "Shopping",
  experience: "Experience",
  hidden_gem: "Hidden gem",
};
