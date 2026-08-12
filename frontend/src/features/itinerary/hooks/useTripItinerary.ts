import { useQuery } from "@tanstack/react-query";

import { fetchTripItinerary } from "../api/itineraryApi";

export const tripItineraryQueryKey = (tripId: string) => ["itinerary", "trip", tripId] as const;

export function useTripItinerary(tripId: string) {
  return useQuery({
    queryKey: tripItineraryQueryKey(tripId),
    queryFn: () => fetchTripItinerary(tripId),
    enabled: Boolean(tripId),
  });
}
