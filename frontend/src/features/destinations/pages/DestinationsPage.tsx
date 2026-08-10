import { useState } from "react";

import { EmptyState } from "../../../components/ui/EmptyState";
import { ErrorState } from "../../../components/ui/ErrorState";
import { Spinner } from "../../../components/ui/Spinner";
import { DestinationCard } from "../components/DestinationCard";
import { useDestinationSearch } from "../hooks/useDestinationSearch";

export function DestinationsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const { data, isLoading, isFetching, isError, error, refetch } = useDestinationSearch(searchTerm, {
    includeEmpty: true,
  });

  return (
    <main className="min-h-screen bg-[var(--bg)] px-5 py-12 text-[var(--text)] sm:px-8">
      <div className="mx-auto max-w-6xl">
        <header className="mb-8">
          <span className="section-kicker">Discover</span>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">Browse destinations</h1>
          <p className="mt-3 max-w-2xl text-neutral">
            Search by destination, city, or country. Results are cached per search so returning to a previous query is instant.
          </p>
        </header>

        <div className="mb-8 flex flex-col gap-3 sm:flex-row sm:items-center">
          <label className="sr-only" htmlFor="destination-search">Search destinations</label>
          <div className="relative flex-1">
            <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-neutral" aria-hidden="true">⌕</span>
            <input
              id="destination-search"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search destinations..."
              autoComplete="off"
              className="w-full rounded-2xl border border-[var(--line)] bg-[var(--surface-solid)] px-11 py-3.5 text-[var(--text)] outline-none transition focus:border-[var(--accent)]"
            />
          </div>
          {isFetching && !isLoading ? <Spinner label="Updating results..." /> : null}
        </div>

        {isLoading ? <Spinner label="Searching destinations..." /> : null}

        {isError ? (
          <ErrorState
            title="Destinations unavailable"
            message={error instanceof Error ? error.message : "We couldn't load destinations right now. Please try again."}
            onRetry={() => void refetch()}
          />
        ) : null}

        {data && data.results.length === 0 ? (
          <EmptyState message="No destinations found. Try a different search term." />
        ) : null}

        {data && data.results.length > 0 ? (
          <>
            <div className="mb-4 flex items-center justify-between text-sm text-neutral">
              <span>{data.count} destination{data.count === 1 ? "" : "s"}</span>
              {data.next ? <span>More destinations available</span> : null}
            </div>
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {data.results.map((destination) => (
                <DestinationCard key={destination.id} destination={destination} />
              ))}
            </div>
          </>
        ) : null}
      </div>
    </main>
  );
}
