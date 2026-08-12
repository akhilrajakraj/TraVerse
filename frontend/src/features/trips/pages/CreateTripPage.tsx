import { useState, type FormEvent } from "react";

import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { ErrorState } from "../../../components/ui/ErrorState";
import type { Destination } from "../../destinations/api/destinationsApi";
import { DestinationPicker } from "../components/DestinationPicker";
import { useCreateTrip } from "../hooks/useCreateTrip";

export function CreateTripPage() {
  const createTrip = useCreateTrip();
  const [title, setTitle] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [travelerCount, setTravelerCount] = useState("1");
  const [notes, setNotes] = useState("");
  const [destinations, setDestinations] = useState<Destination[]>([]);
  const [validationError, setValidationError] = useState<string | null>(null);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setValidationError(null);

    if (startDate && endDate && endDate < startDate) {
      setValidationError("The end date must be on or after the start date.");
      return;
    }

    const parsedTravelerCount = Number(travelerCount);
    if (!Number.isInteger(parsedTravelerCount) || parsedTravelerCount < 1) {
      setValidationError("Traveler count must be at least 1.");
      return;
    }

    createTrip.mutate({
      title: title.trim(),
      start_date: startDate,
      end_date: endDate,
      destination_ids: destinations.map((destination) => destination.id),
      traveler_count: parsedTravelerCount,
      notes: notes.trim(),
    });
  }

  return (
    <div className="workspace-view">
      <section className="mb-6">
        <span className="section-kicker">Trips</span>
        <h1 className="mt-2 font-serif text-4xl font-semibold tracking-tight">Plan a new trip.</h1>
        <p className="mt-3 max-w-2xl text-neutral">
          Set the basics now. Itinerary, budget, recommendations, and AI planning will build on this trip later.
        </p>
      </section>

      <Card className="max-w-3xl">
        {validationError ? <div className="mb-4"><ErrorState message={validationError} /></div> : null}
        {createTrip.isError ? (
          <div className="mb-4">
            <ErrorState
              title="Trip creation failed"
              message={createTrip.error instanceof Error ? createTrip.error.message : "We couldn't create this trip right now."}
            />
          </div>
        ) : null}

        <form onSubmit={handleSubmit} className="grid gap-5">
          <label className="grid gap-2 text-sm font-semibold">
            Trip title
            <input
              required
              maxLength={200}
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Summer in Japan"
              className="rounded-xl border border-[var(--line)] bg-[var(--surface-solid)] px-4 py-3 font-normal text-[var(--text)] outline-none focus:border-[var(--accent)]"
            />
          </label>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="grid gap-2 text-sm font-semibold">
              Start date
              <input
                required
                type="date"
                value={startDate}
                onChange={(event) => setStartDate(event.target.value)}
                className="rounded-xl border border-[var(--line)] bg-[var(--surface-solid)] px-4 py-3 font-normal text-[var(--text)] outline-none focus:border-[var(--accent)]"
              />
            </label>
            <label className="grid gap-2 text-sm font-semibold">
              End date
              <input
                required
                type="date"
                value={endDate}
                min={startDate || undefined}
                onChange={(event) => setEndDate(event.target.value)}
                className="rounded-xl border border-[var(--line)] bg-[var(--surface-solid)] px-4 py-3 font-normal text-[var(--text)] outline-none focus:border-[var(--accent)]"
              />
            </label>
          </div>

          <label className="grid max-w-xs gap-2 text-sm font-semibold">
            Travelers
            <input
              required
              min={1}
              type="number"
              value={travelerCount}
              onChange={(event) => setTravelerCount(event.target.value)}
              className="rounded-xl border border-[var(--line)] bg-[var(--surface-solid)] px-4 py-3 font-normal text-[var(--text)] outline-none focus:border-[var(--accent)]"
            />
          </label>

          <DestinationPicker selected={destinations} onChange={setDestinations} />

          <label className="grid gap-2 text-sm font-semibold">
            Notes <span className="font-normal text-neutral">(optional)</span>
            <textarea
              rows={4}
              maxLength={5000}
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Anything important about this trip..."
              className="rounded-xl border border-[var(--line)] bg-[var(--surface-solid)] px-4 py-3 font-normal text-[var(--text)] outline-none focus:border-[var(--accent)]"
            />
          </label>

          <div className="flex flex-col-reverse gap-3 border-t border-[var(--line)] pt-5 sm:flex-row sm:justify-end">
            <Button type="button" variant="secondary" onClick={() => window.history.back()}>
              Cancel
            </Button>
            <Button type="submit" isLoading={createTrip.isPending}>
              Create trip
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
