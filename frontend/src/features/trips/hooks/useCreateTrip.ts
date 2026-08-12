import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { routes } from "../../../routes/routeConfig";
import { createTrip, type CreateTripPayload } from "../api/tripsApi";
import { TRIPS_LIST_QUERY_KEY } from "./useTrips";

export function useCreateTrip() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (payload: CreateTripPayload) => createTrip(payload),
    onSuccess: (newTrip) => {
      queryClient.invalidateQueries({ queryKey: TRIPS_LIST_QUERY_KEY });
      navigate(routes.protected.tripDetail.replace(":tripId", newTrip.id));
    },
  });
}
