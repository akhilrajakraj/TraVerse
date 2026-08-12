import { useMutation, useQueryClient } from "@tanstack/react-query";

import { tripRecommendationsQueryKey } from "../../recommendations/hooks/useTripRecommendations";
import { tripBudgetQueryKey } from "../../budget/hooks/useTripBudget";
import { tripItineraryQueryKey } from "../../itinerary/hooks/useTripItinerary";
import { tripPlanStatusQueryKey } from "./useTripPlanStatus";
import { triggerTripPlan } from "../api/aiPlannerApi";

export function useTriggerTripPlan() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (tripId: string) => triggerTripPlan(tripId),
    onSuccess: (_response, tripId) => {
      void queryClient.invalidateQueries({
        queryKey: tripPlanStatusQueryKey(tripId),
      });
    },
    onSettled: (_response, _error, tripId) => {
      if (!_error) return;

      // Keep the existing authoritative trip-detail caches untouched when
      // queueing itself fails. The successful worker completion is responsible
      // for refreshing generated trip sub-domain data.
    },
  });
}

export function invalidateGeneratedTripData(
  queryClient: ReturnType<typeof useQueryClient>,
  tripId: string,
) {
  return Promise.all([
    queryClient.invalidateQueries({ queryKey: ["trips", tripId] }),
    queryClient.invalidateQueries({ queryKey: tripItineraryQueryKey(tripId) }),
    queryClient.invalidateQueries({ queryKey: tripBudgetQueryKey(tripId) }),
    queryClient.invalidateQueries({ queryKey: tripRecommendationsQueryKey(tripId) }),
  ]);
}
