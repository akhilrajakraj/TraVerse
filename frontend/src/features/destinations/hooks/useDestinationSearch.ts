import { useQuery } from "@tanstack/react-query";

import { useDebounce } from "../../../hooks/useDebounce";
import { searchDestinations } from "../api/destinationsApi";

export function useDestinationSearch(searchTerm: string) {
  const debouncedTerm = useDebounce(searchTerm, 400).trim();

  return useQuery({
    queryKey: ["destinations", "search", debouncedTerm],
    queryFn: () => searchDestinations(debouncedTerm),
    enabled: debouncedTerm.length > 0,
    staleTime: 5 * 60 * 1000,
  });
}
