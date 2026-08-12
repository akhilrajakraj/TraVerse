import { useMutation, useQueryClient } from "@tanstack/react-query";

import { acceptRecommendation } from "../api/recommendationsApi";
import { tripRecommendationsQueryKey } from "./useTripRecommendations";

interface AcceptRecommendationVariables {
  recommendationId: string;
  tripId: string;
}

export function useAcceptRecommendation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ recommendationId }: AcceptRecommendationVariables) =>
      acceptRecommendation(recommendationId),
    onSuccess: (_recommendation, variables) => {
      queryClient.invalidateQueries({
        queryKey: tripRecommendationsQueryKey(variables.tripId),
      });
    },
  });
}
