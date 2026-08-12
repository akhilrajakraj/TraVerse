import { useQuery } from "@tanstack/react-query";

import { fetchTripBudget } from "../api/budgetApi";

export const tripBudgetQueryKey = (tripId: string) => [
  "budget",
  "trip",
  tripId,
] as const;

export function useTripBudget(tripId: string) {
  return useQuery({
    queryKey: tripBudgetQueryKey(tripId),
    queryFn: () => fetchTripBudget(tripId),
    enabled: Boolean(tripId),
  });
}
