import { useQuery } from "@tanstack/react-query";

import { useDebounce } from "../../../hooks/useDebounce";
import { getDestinations, type Destination } from "../api/destinationsApi";

export function useDestinationSearch(searchTerm: string) {
  const debouncedTerm = useDebounce(searchTerm, 400).trim().toLowerCase();

  const query = useQuery({
    queryKey: ["destinations", "catalog"],
    queryFn: getDestinations,
    enabled: debouncedTerm.length > 0,
    staleTime: 5 * 60 * 1000,
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
