import { useMemo, useState } from "react";

import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { EmptyState } from "../../../components/ui/EmptyState";
import { ErrorState } from "../../../components/ui/ErrorState";
import { Spinner } from "../../../components/ui/Spinner";
import { StatusBadge } from "../../../components/ui/StatusBadge";
import { recommendationStatusColors } from "../../../lib/statusColors";
import {
  recommendationCategoryLabels,
  type Recommendation,
  type RecommendationStatus,
} from "../api/recommendationsApi";
import { useAcceptRecommendation } from "../hooks/useAcceptRecommendation";
import { useRejectRecommendation } from "../hooks/useRejectRecommendation";
import { useTripRecommendations } from "../hooks/useTripRecommendations";

interface TripRecommendationsPanelProps {
  tripId: string;
}

type RecommendationFilter = "all" | RecommendationStatus;

const filters: Array<{ value: RecommendationFilter; label: string }> = [
  { value: "all", label: "All" },
  { value: "pending", label: "Pending" },
  { value: "accepted", label: "Accepted" },
  { value: "rejected", label: "Rejected" },
];

function formatScore(score: string) {
  const numericScore = Number(score);
  if (Number.isNaN(numericScore)) return score;
  return `${Math.round(numericScore * 100)}% match`;
}

function getDestinationLabel(recommendation: Recommendation) {
  const { city, country } = recommendation.destination;
  return city ? `${city}, ${country}` : country;
}

export function TripRecommendationsPanel({ tripId }: TripRecommendationsPanelProps) {
  const recommendations = useTripRecommendations(tripId);
  const accept = useAcceptRecommendation();
  const reject = useRejectRecommendation();
  const [filter, setFilter] = useState<RecommendationFilter>("all");

  const visibleRecommendations = useMemo(() => {
    const items = recommendations.data?.results ?? [];

    if (filter === "all") return items;
    return items.filter((item) => item.status === filter);
  }, [filter, recommendations.data?.results]);

  function handleAccept(recommendationId: string) {
    accept.mutate({ recommendationId, tripId });
  }

  function handleReject(recommendationId: string) {
    reject.mutate({ recommendationId, tripId });
  }

  if (recommendations.isLoading) {
    return <Spinner label="Loading recommendations..." />;
  }

  if (recommendations.isError || !recommendations.data) {
    return (
      <ErrorState
        title="Recommendations unavailable"
        message={
          recommendations.error instanceof Error
            ? recommendations.error.message
            : "We couldn't load recommendations for this trip."
        }
        onRetry={() => void recommendations.refetch()}
      />
    );
  }

  const allRecommendations = recommendations.data.results;

  return (
    <section
      className="mt-8 border-t border-[var(--line)] pt-6"
      aria-labelledby="recommendations-heading"
    >
      <div className="mb-5">
        <span className="section-kicker">Recommendations</span>
        <h2 id="recommendations-heading" className="mt-1 text-xl font-semibold">
          Places worth considering
        </h2>
        <p className="mt-2 text-sm text-neutral">
          Review destination suggestions, understand why they were selected, and keep only the ones that fit your trip.
        </p>
      </div>

      {allRecommendations.length > 0 ? (
        <div className="mb-5 flex flex-wrap gap-2" aria-label="Recommendation filters">
          {filters.map((option) => {
            const count =
              option.value === "all"
                ? allRecommendations.length
                : allRecommendations.filter((item) => item.status === option.value).length;

            return (
              <button
                key={option.value}
                type="button"
                onClick={() => setFilter(option.value)}
                aria-pressed={filter === option.value}
                className={`rounded-full border px-3 py-1.5 text-sm font-semibold transition ${
                  filter === option.value
                    ? "border-orange-500 bg-orange-50 text-[var(--text)]"
                    : "border-[var(--line)] bg-[var(--surface-solid)] text-neutral hover:border-orange-300"
                }`}
              >
                {option.label} ({count})
              </button>
            );
          })}
        </div>
      ) : null}

      {visibleRecommendations.length === 0 ? (
        <EmptyState
          message={
            allRecommendations.length === 0
              ? "No recommendations are available for this trip yet. AI-generated suggestions will appear here when the recommendation engine produces them."
              : `No ${filter} recommendations are available.`
          }
        />
      ) : (
        <ol className="space-y-4" aria-label="Trip recommendations">
          {visibleRecommendations.map((recommendation) => {
            const isAccepting =
              accept.isPending &&
              accept.variables?.recommendationId === recommendation.id;
            const isRejecting =
              reject.isPending &&
              reject.variables?.recommendationId === recommendation.id;
            const isMutating = accept.isPending || reject.isPending;

            return (
              <li key={recommendation.id}>
                <Card className="overflow-hidden p-0">
                  <div className="flex flex-col sm:flex-row">
                    {recommendation.destination.image_url ? (
                      <img
                        src={recommendation.destination.image_url}
                        alt={recommendation.destination.name}
                        className="h-48 w-full object-cover sm:h-auto sm:w-48"
                      />
                    ) : null}

                    <div className="flex-1 p-5">
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="rounded-full bg-neutral-bg px-2 py-1 text-xs font-bold text-neutral">
                              {recommendationCategoryLabels[recommendation.category]}
                            </span>
                            {recommendation.is_ai_generated ? (
                              <span className="rounded-full bg-info/10 px-2 py-1 text-xs font-bold text-info">
                                AI recommendation
                              </span>
                            ) : null}
                          </div>
                          <h3 className="mt-2 text-lg font-semibold">
                            {recommendation.destination.name}
                          </h3>
                          <p className="mt-1 text-sm text-neutral">
                            {getDestinationLabel(recommendation)}
                          </p>
                        </div>

                        <div className="flex flex-col items-start gap-2 sm:items-end">
                          <StatusBadge
                            status={recommendation.status}
                            colorMap={recommendationStatusColors}
                          />
                          <span className="text-sm font-semibold text-[var(--accent-dark)]">
                            {formatScore(recommendation.score)}
                          </span>
                        </div>
                      </div>

                      <p className="mt-4 text-sm leading-6 text-neutral">
                        {recommendation.reason}
                      </p>

                      {recommendation.status === "pending" ? (
                        <div className="mt-5 flex flex-wrap gap-2">
                          <Button
                            type="button"
                            onClick={() => handleAccept(recommendation.id)}
                            isLoading={isAccepting}
                            disabled={isMutating && !isAccepting}
                          >
                            Keep recommendation
                          </Button>
                          <Button
                            type="button"
                            variant="danger"
                            onClick={() => handleReject(recommendation.id)}
                            isLoading={isRejecting}
                            disabled={isMutating && !isRejecting}
                          >
                            Dismiss
                          </Button>
                        </div>
                      ) : null}

                      {accept.isError && accept.variables?.recommendationId === recommendation.id ? (
                        <p className="mt-3 text-sm text-red-600" role="alert">
                          {accept.error instanceof Error
                            ? accept.error.message
                            : "Unable to accept this recommendation."}
                        </p>
                      ) : null}
                      {reject.isError && reject.variables?.recommendationId === recommendation.id ? (
                        <p className="mt-3 text-sm text-red-600" role="alert">
                          {reject.error instanceof Error
                            ? reject.error.message
                            : "Unable to dismiss this recommendation."}
                        </p>
                      ) : null}
                    </div>
                  </div>
                </Card>
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}
