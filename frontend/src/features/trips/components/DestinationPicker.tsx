import { useState } from "react";

import type { Destination } from "../../destinations/api/destinationsApi";
import { useDestinationSearch } from "../../destinations/hooks/useDestinationSearch";

interface DestinationPickerProps {
  selected: Destination[];
  onChange: (destinations: Destination[]) => void;
}

export function DestinationPicker({ selected, onChange }: DestinationPickerProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const { data, isLoading, isError } = useDestinationSearch(searchTerm);

  function addDestination(destination: Destination) {
    if (!selected.some((item) => item.id === destination.id)) {
      onChange([...selected, destination]);
    }
    setSearchTerm("");
  }

  function removeDestination(id: string) {
    onChange(selected.filter((destination) => destination.id !== id));
  }

  const results = data?.results.filter(
    (destination) => !selected.some((item) => item.id === destination.id),
  ) ?? [];

  return (
    <fieldset className="grid gap-3">
      <legend className="text-sm font-semibold text-[var(--text)]">Destinations</legend>

      {selected.length > 0 ? (
        <div className="flex flex-wrap gap-2" aria-label="Selected destinations">
          {selected.map((destination) => (
            <span
              key={destination.id}
              className="inline-flex items-center gap-2 rounded-full bg-info-bg px-3 py-1.5 text-xs font-medium text-info"
            >
              {destination.name}
              <button
                type="button"
                onClick={() => removeDestination(destination.id)}
                aria-label={`Remove ${destination.name}`}
                className="font-bold leading-none"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      ) : (
        <p className="text-sm text-neutral">Add one or more destinations to your trip.</p>
      )}

      <div className="relative">
        <label className="sr-only" htmlFor="destination-picker-search">
          Search destinations to add
        </label>
        <input
          id="destination-picker-search"
          value={searchTerm}
          onChange={(event) => setSearchTerm(event.target.value)}
          placeholder="Search destinations to add..."
          autoComplete="off"
          className="w-full rounded-xl border border-[var(--line)] bg-[var(--surface-solid)] px-4 py-3 text-[var(--text)] outline-none transition focus:border-[var(--accent)]"
        />

        {searchTerm.trim() && (
          <div className="mt-2 overflow-hidden rounded-xl border border-[var(--line)] bg-[var(--surface-solid)]">
            {isLoading ? <p className="px-4 py-3 text-sm text-neutral">Searching destinations...</p> : null}
            {isError ? <p className="px-4 py-3 text-sm text-danger">Destinations are unavailable right now.</p> : null}
            {!isLoading && !isError && results.length === 0 ? (
              <p className="px-4 py-3 text-sm text-neutral">No matching destinations.</p>
            ) : null}
            {!isLoading && !isError && results.length > 0 ? (
              <ul className="max-h-52 overflow-y-auto py-1" aria-label="Destination search results">
                {results.map((destination) => (
                  <li key={destination.id}>
                    <button
                      type="button"
                      onClick={() => addDestination(destination)}
                      className="w-full px-4 py-3 text-left text-sm transition hover:bg-neutral-bg"
                    >
                      <span className="font-medium">{destination.name}</span>
                      <span className="ml-2 text-neutral">{destination.city}, {destination.country}</span>
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        )}
      </div>
    </fieldset>
  );
}
