import { useQuery } from "@tanstack/react-query";

import { fetchTrip } from "../api/tripsApi";

export function useTrip(tripId: string) {
  return useQuery({
    queryKey: ["trips", tripId],
    queryFn: () => fetchTrip(tripId),
    enabled: Boolean(tripId),
  });
}
