import { useMutation, useQueryClient } from "@tanstack/react-query";

import { addItineraryItem, type AddItineraryItemPayload } from "../api/itineraryApi";
import { tripItineraryQueryKey } from "./useTripItinerary";

interface AddItineraryItemVariables {
  dayId: string;
  tripId: string;
  payload: AddItineraryItemPayload;
}

export function useAddItineraryItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ dayId, payload }: AddItineraryItemVariables) => addItineraryItem(dayId, payload),
    onSuccess: (_response, variables) => {
      queryClient.invalidateQueries({ queryKey: tripItineraryQueryKey(variables.tripId) });
    },
  });
}
