import { useQuery } from "@tanstack/react-query";

import { fetchTripRecommendations } from "../api/recommendationsApi";

export const tripRecommendationsQueryKey = (tripId: string) =>
  ["recommendations", "trip", tripId] as const;

export function useTripRecommendations(tripId: string) {
  return useQuery({
    queryKey: tripRecommendationsQueryKey(tripId),
    queryFn: () => fetchTripRecommendations(tripId),
    enabled: Boolean(tripId),
  });
}
