import { useState, type FormEvent } from "react";

import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { EmptyState } from "../../../components/ui/EmptyState";
import { ErrorState } from "../../../components/ui/ErrorState";
import { Input } from "../../../components/ui/Input";
import { Spinner } from "../../../components/ui/Spinner";
import { GeneratedItineraryReview } from "./GeneratedItineraryReview";
import { useAddItineraryItem } from "../hooks/useAddItineraryItem";
import { useTripItinerary } from "../hooks/useTripItinerary";

interface TripItineraryPanelProps {
  tripId: string;
}

function normalizeOptional(value: string) {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}

export function TripItineraryPanel({ tripId }: TripItineraryPanelProps) {
  const itinerary = useTripItinerary(tripId);
  const addItem = useAddItineraryItem();
  const [activeDayId, setActiveDayId] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [startTime, setStartTime] = useState("");
  const [estimatedCost, setEstimatedCost] = useState("");
  const [validationError, setValidationError] = useState("");

  if (itinerary.isLoading) return <Spinner label="Loading itinerary..." />;

  if (itinerary.isError) {
    return (
      <ErrorState
        title="Itinerary unavailable"
        message={itinerary.error instanceof Error ? itinerary.error.message : "We couldn't load this trip itinerary."}
        onRetry={() => void itinerary.refetch()}
      />
    );
  }

  const days = itinerary.data ?? [];

  if (days.length === 0) {
    return (
      <EmptyState message="No itinerary days exist for this trip yet. AI-generated itinerary days will appear here once the planner creates them." />
    );
  }

  const selectedDayId = activeDayId ?? days[0]?.id ?? null;
  const selectedDay = days.find((day) => day.id === selectedDayId) ?? days[0];

  function resetForm() {
    setTitle("");
    setDescription("");
    setStartTime("");
    setEstimatedCost("");
    setValidationError("");
  }

  function handleSubmit(dayId: string) {
    return (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      const trimmedTitle = title.trim();

      if (!trimmedTitle) {
        setValidationError("Activity title is required.");
        return;
      }

      setValidationError("");
      addItem.mutate(
        {
          dayId,
          tripId,
          payload: {
            title: trimmedTitle,
            description: normalizeOptional(description),
            start_time: normalizeOptional(startTime) ?? null,
            estimated_cost_usd: normalizeOptional(estimatedCost) ?? null,
          },
        },
        { onSuccess: resetForm },
      );
    };
  }

  return (
    <section className="mt-8 border-t border-[var(--line)] pt-6" aria-labelledby="itinerary-heading">
      <div className="mb-5">
        <span className="section-kicker">Itinerary</span>
        <h2 id="itinerary-heading" className="mt-1 text-xl font-semibold">Day-by-day planner</h2>
        <p className="mt-2 text-sm text-neutral">Review each day in order and add hand-authored activities to existing itinerary days.</p>
      </div>

      <div className="grid gap-5 lg:grid-cols-[220px_1fr]">
        <nav className="flex gap-2 overflow-x-auto lg:flex-col" aria-label="Itinerary days">
          {days.map((day) => (
            <button
              key={day.id}
              type="button"
              onClick={() => setActiveDayId(day.id)}
              className={`rounded-xl border px-4 py-3 text-left transition ${selectedDayId === day.id ? "border-orange-500 bg-orange-50 text-[var(--text)]" : "border-[var(--line)] bg-[var(--surface-solid)] text-neutral hover:border-orange-300"}`}
            >
              <span className="block text-sm font-bold">Day {day.day_number}</span>
              <span className="block text-xs">{day.date}</span>
            </button>
          ))}
        </nav>

        <div className="space-y-4">
          {selectedDay ? (
            <div className="space-y-4">
              {selectedDay.summary ? <p className="rounded-xl bg-[var(--surface-muted)] p-4 text-sm text-neutral">{selectedDay.summary}</p> : null}

              <GeneratedItineraryReview day={selectedDay} />

              <Card className="p-4">
                <form className="space-y-3" onSubmit={handleSubmit(selectedDay.id)}>
                  <h3 className="font-semibold">Add activity to day {selectedDay.day_number}</h3>
                  <Input label="Activity title" value={title} onChange={(event) => setTitle(event.target.value)} error={validationError} />
                  <Input label="Description" value={description} onChange={(event) => setDescription(event.target.value)} />
                  <div className="grid gap-3 sm:grid-cols-2">
                    <Input label="Start time" type="time" value={startTime} onChange={(event) => setStartTime(event.target.value)} />
                    <Input label="Estimated cost USD" type="number" min="0" step="0.01" value={estimatedCost} onChange={(event) => setEstimatedCost(event.target.value)} />
                  </div>
                  {addItem.isError ? <p className="text-sm text-red-600" role="alert">{addItem.error instanceof Error ? addItem.error.message : "Unable to add this activity."}</p> : null}
                  <Button type="submit" isLoading={addItem.isPending}>Add activity</Button>
                </form>
              </Card>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
