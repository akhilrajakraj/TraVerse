import { useMutation, useQueryClient } from "@tanstack/react-query";

import { rejectRecommendation } from "../api/recommendationsApi";
import { tripRecommendationsQueryKey } from "./useTripRecommendations";

interface RejectRecommendationVariables {
  recommendationId: string;
  tripId: string;
}

export function useRejectRecommendation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ recommendationId }: RejectRecommendationVariables) =>
      rejectRecommendation(recommendationId),
    onSuccess: (_recommendation, variables) => {
      queryClient.invalidateQueries({
        queryKey: tripRecommendationsQueryKey(variables.tripId),
      });
    },
  });
}
