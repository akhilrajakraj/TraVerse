import { Card } from "../../../components/ui/Card";
import type { Destination } from "../api/destinationsApi";

export function DestinationCard({ destination }: { destination: Destination }) {
  return (
    <Card className="overflow-hidden p-0 transition-transform duration-200 hover:-translate-y-0.5">
      {destination.image_url ? (
        <img
          src={destination.image_url}
          alt={destination.name}
          className="h-44 w-full object-cover"
          loading="lazy"
        />
      ) : (
        <div
          className="flex h-44 items-center justify-center bg-[var(--surface-muted)] text-4xl"
          aria-hidden="true"
        >
          ✦
        </div>
      )}
      <div className="p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold">{destination.name}</h2>
            <p className="text-sm text-neutral">{destination.city}, {destination.country}</p>
          </div>
          <span className="rounded-full bg-[var(--surface-muted)] px-2.5 py-1 text-xs text-neutral">
            Explore
          </span>
        </div>
      </div>
    </Card>
  );
}
