import { Link, useParams } from "react-router-dom";

import { Card } from "../../../components/ui/Card";
import { ErrorState } from "../../../components/ui/ErrorState";
import { Spinner } from "../../../components/ui/Spinner";
import { StatusBadge } from "../../../components/ui/StatusBadge";
import { routes } from "../../../routes/routeConfig";
import { tripStatusColors } from "../../../lib/statusColors";
import { TripBudgetPanel } from "../../budget/components/TripBudgetPanel";
import { TripItineraryPanel } from "../../itinerary/components/TripItineraryPanel";
import { TripRecommendationsPanel } from "../../recommendations/components/TripRecommendationsPanel";
import { useTrip } from "../hooks/useTrip";

export function TripDetailPage() {
  const { tripId } = useParams<{ tripId: string }>();
  const { data: trip, isLoading, isError, error, refetch } = useTrip(tripId ?? "");

  if (isLoading) {
    return <Spinner label="Loading trip..." />;
  }

  if (isError || !trip) {
    return (
      <div className="workspace-view">
        <ErrorState
          title="Trip unavailable"
          message={error instanceof Error ? error.message : "We couldn't find this trip."}
          onRetry={() => void refetch()}
        />
      </div>
    );
  }

  return (
    <div className="workspace-view">
      <div className="mb-6">
        <Link to={routes.protected.dashboard} className="text-sm font-semibold text-[var(--accent-dark)] hover:underline">
          ← Back to trips
        </Link>
      </div>

      <section className="workspace-page-card">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <span className="section-kicker">Trip</span>
            <h1>{trip.title}</h1>
            <p>{trip.start_date} — {trip.end_date} · {trip.duration_days} days</p>
          </div>
          <StatusBadge status={trip.status} colorMap={tripStatusColors} />
        </div>

        <div className="mt-7 grid gap-3 sm:grid-cols-3">
          <Card>
            <span className="text-xs font-bold uppercase tracking-wide text-neutral">Travelers</span>
            <strong className="mt-2 block text-xl">{trip.traveler_count}</strong>
          </Card>
          <Card>
            <span className="text-xs font-bold uppercase tracking-wide text-neutral">Destinations</span>
            <strong className="mt-2 block text-xl">{trip.destinations.length}</strong>
          </Card>
          <Card>
            <span className="text-xs font-bold uppercase tracking-wide text-neutral">Budget</span>
            <strong className="mt-2 block text-xl">{trip.computed_budget_total ?? "Not set"}</strong>
          </Card>
        </div>

        {trip.destinations.length > 0 ? (
          <section className="mt-7">
            <h2 className="text-lg font-semibold">Destinations</h2>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              {trip.destinations.map((destination) => (
                <Card key={destination.id} className="p-4">
                  <strong>{destination.name}</strong>
                  <p className="mt-1 text-sm text-neutral">{destination.city}, {destination.country}</p>
                </Card>
              ))}
            </div>
          </section>
        ) : null}

        {trip.notes ? (
          <section className="mt-7">
            <h2 className="text-lg font-semibold">Notes</h2>
            <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-neutral">{trip.notes}</p>
          </section>
        ) : null}

        <TripItineraryPanel tripId={trip.id} />
        <TripBudgetPanel tripId={trip.id} />
        <TripRecommendationsPanel tripId={trip.id} />
      </section>
    </div>
  );
}
