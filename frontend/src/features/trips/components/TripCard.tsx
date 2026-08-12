import { Link } from "react-router-dom";

import { Card } from "../../../components/ui/Card";
import { StatusBadge } from "../../../components/ui/StatusBadge";
import { routes } from "../../../routes/routeConfig";
import { tripStatusColors } from "../../../lib/statusColors";
import type { Trip } from "../api/tripsApi";

export function TripCard({ trip }: { trip: Trip }) {
  return (
    <Link
      to={routes.protected.tripDetail.replace(":tripId", trip.id)}
      className="block rounded-2xl focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]"
    >
      <Card className="h-full transition duration-200 hover:-translate-y-0.5 hover:shadow-md">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <h2 className="truncate text-lg font-semibold">{trip.title}</h2>
            <p className="mt-1 text-sm text-neutral">
              {trip.start_date} — {trip.end_date}
            </p>
          </div>
          <StatusBadge status={trip.status} colorMap={tripStatusColors} />
        </div>

        <div className="mt-5 flex flex-wrap gap-x-5 gap-y-2 text-sm text-neutral">
          <span>{trip.duration_days} day{trip.duration_days === 1 ? "" : "s"}</span>
          <span>{trip.traveler_count} traveler{trip.traveler_count === 1 ? "" : "s"}</span>
          <span>{trip.destinations.length} destination{trip.destinations.length === 1 ? "" : "s"}</span>
        </div>
      </Card>
    </Link>
  );
}
