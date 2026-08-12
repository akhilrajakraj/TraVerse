import { useQuery } from "@tanstack/react-query";

import { fetchTrips } from "../api/tripsApi";

export const TRIPS_LIST_QUERY_KEY = ["trips", "list"] as const;

export function useTrips() {
  return useQuery({
    queryKey: TRIPS_LIST_QUERY_KEY,
    queryFn: fetchTrips,
  });
}
