import { useQuery } from "@tanstack/react-query";

import { useDebounce } from "../../../hooks/useDebounce";
import { getDestinations, type Destination } from "../api/destinationsApi";

const DESTINATIONS_QUERY_KEY = ["destinations", "catalog"] as const;
const DESTINATIONS_STALE_TIME = 5 * 60 * 1000;

export function useDestinationSearch(searchTerm: string) {
  const debouncedTerm = useDebounce(searchTerm, 400).trim().toLowerCase();

  const query = useQuery({
    queryKey: DESTINATIONS_QUERY_KEY,
    queryFn: getDestinations,
    // The backend exposes one active catalog endpoint. An empty search term
    // must browse that catalog, so the query is always enabled.
    staleTime: DESTINATIONS_STALE_TIME,
  });

  const results = query.data?.results.filter((destination: Destination) => {
    if (!debouncedTerm) return true;

    const searchableText = [
      destination.name,
      destination.country,
      destination.city,
    ]
      .join(" ")
      .toLowerCase();

    return searchableText.includes(debouncedTerm);
  });

  return {
    ...query,
    data: query.data
      ? {
          ...query.data,
          count: results?.length ?? 0,
          results: results ?? [],
        }
      : undefined,
  };
}
