import { useQuery } from "@tanstack/react-query";

import { useDebounce } from "../../../hooks/useDebounce";
import { searchDestinations } from "../api/destinationsApi";

interface DestinationSearchOptions {
  /**
   * When true, an empty search term loads the complete destination list.
   * Consumers that are only searching should leave this disabled so the
   * hook does not perform an unnecessary request before the first term.
   */
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
  });
}
