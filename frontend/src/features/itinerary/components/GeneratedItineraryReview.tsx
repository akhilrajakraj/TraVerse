import { Card } from "../../../components/ui/Card";
import type { ItineraryDay, ItineraryItem } from "../api/itineraryApi";

interface GeneratedItineraryReviewProps {
  day: ItineraryDay;
}

function formatCurrency(value: string | null) {
  if (!value) return null;
  const amount = Number(value);
  if (Number.isNaN(amount)) return `$${value}`;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(amount);
}

function ItineraryItemCard({ item }: { item: ItineraryItem }) {
  const cost = formatCurrency(item.estimated_cost_usd);

  return (
    <Card
      className={
        item.is_ai_generated
          ? "border-info/30 bg-info/5 p-4"
          : "border-[var(--line)] bg-[var(--surface-solid)] p-4"
      }
    >
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-neutral-bg px-2 py-1 text-xs font-bold text-neutral">
              #{item.order}
            </span>
            <span
              className={
                item.is_ai_generated
                  ? "rounded-full bg-info/10 px-2 py-1 text-xs font-bold text-info"
                  : "rounded-full bg-neutral-bg px-2 py-1 text-xs font-bold text-neutral"
              }
            >
              {item.is_ai_generated ? "AI-generated" : "Added by you"}
            </span>
          </div>

          <h3 className="mt-2 font-semibold">{item.title}</h3>
          {item.description ? <p className="mt-1 text-sm text-neutral">{item.description}</p> : null}
          {item.destination ? (
            <p className="mt-2 text-xs text-neutral">
              {item.destination.name}, {item.destination.city}
            </p>
          ) : null}
        </div>

        <div className="shrink-0 text-sm text-neutral sm:text-right">
          {item.start_time ? <p>{item.start_time}</p> : null}
          {cost ? <p>{cost}</p> : null}
        </div>
      </div>
    </Card>
  );
}

export function GeneratedItineraryReview({ day }: GeneratedItineraryReviewProps) {
  return (
    <div className="space-y-4">
      {day.items.length > 0 ? (
        <ol className="space-y-3" aria-label={`Activities for day ${day.day_number}`}>
          {day.items.map((item) => (
            <li key={item.id}>
              <ItineraryItemCard item={item} />
            </li>
          ))}
        </ol>
      ) : (
        <p className="rounded-xl border border-dashed border-[var(--line)] p-4 text-sm text-neutral">
          Day {day.day_number} does not have activities yet.
        </p>
      )}
    </div>
  );
}
