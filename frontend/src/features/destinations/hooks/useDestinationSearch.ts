import { useQuery } from "@tanstack/react-query";

import { useDebounce } from "../../../hooks/useDebounce";
import { searchDestinations } from "../api/destinationsApi";

interface DestinationSearchOptions {
  /** Load the complete destination list when the search term is empty. */
  includeEmpty?: boolean;
}

export function useDestinationSearch(
  searchTerm: string,
  options: DestinationSearchOptions = {},
) {
  const debouncedTerm = useDebounce(searchTerm, 400).trim();
  const includeEmpty = options.includeEmpty ?? false;

  return useQuery({
    queryKey: ["destinations", "search", debouncedTerm],
    queryFn: () => searchDestinations(debouncedTerm),
    enabled: includeEmpty || debouncedTerm.length > 0,
    staleTime: 5 * 60 * 1000,
  });
}
