import { useMutation, useQueryClient } from "@tanstack/react-query";

import { triggerTripPlan } from "../api/aiPlannerApi";
import { tripPlanStatusQueryKey } from "./useTripPlanStatus";

export function useTriggerTripPlan() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (tripId: string) => triggerTripPlan(tripId),
    onSuccess: (_response, tripId) => {
      void queryClient.invalidateQueries({
        queryKey: tripPlanStatusQueryKey(tripId),
      });
    },
  });
}
