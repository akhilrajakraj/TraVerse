import { Link } from "react-router-dom";

import { Button } from "../../../components/ui/Button";
import { EmptyState } from "../../../components/ui/EmptyState";
import { ErrorState } from "../../../components/ui/ErrorState";
import { Spinner } from "../../../components/ui/Spinner";
import { routes } from "../../../routes/routeConfig";
import { useTrips } from "../../trips/hooks/useTrips";
import { TripCard } from "../../trips/components/TripCard";
import { useAuth } from "../../auth/hooks/useAuth";

export function DashboardView() {
  const { user } = useAuth();
  const { data, isLoading, isError, error, refetch } = useTrips();

  return (
    <div className="workspace-view">
      <section className="workspace-hero">
        <div>
          <span className="section-kicker">Your travel workspace</span>
          <h1>Welcome back{user?.first_name ? `, ${user.first_name}` : ""}.</h1>
          <p>Keep your journeys organized from the first destination to the final day.</p>
        </div>
        <Link to={routes.protected.createTrip} className="workspace-primary-action">
          Plan a trip <span>→</span>
        </Link>
      </section>

      <section className="mt-8">
        <div className="mb-5 flex items-end justify-between gap-4">
          <div>
            <span className="section-kicker">Your trips</span>
            <h2 className="mt-1 text-2xl font-semibold">Trips dashboard</h2>
          </div>
          {data ? <span className="text-sm text-neutral">{data.count} trip{data.count === 1 ? "" : "s"}</span> : null}
        </div>

        {isLoading ? <Spinner label="Loading your trips..." /> : null}

        {isError ? (
          <ErrorState
            title="Trips unavailable"
            message={error instanceof Error ? error.message : "We couldn't load your trips right now."}
            onRetry={() => void refetch()}
          />
        ) : null}

        {data && data.results.length === 0 ? (
          <EmptyState
            message="You haven't planned any trips yet."
            action={(
              <Link to={routes.protected.createTrip}>
                <Button>Plan your first trip</Button>
              </Link>
            )}
          />
        ) : null}

        {data && data.results.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2">
            {data.results.map((trip) => <TripCard key={trip.id} trip={trip} />)}
          </div>
        ) : null}
      </section>
    </div>
  );
}
