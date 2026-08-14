import { useMemo, useState } from "react";

import { Card } from "../../../components/ui/Card";
import { EmptyState } from "../../../components/ui/EmptyState";
import { ErrorState } from "../../../components/ui/ErrorState";
import { Spinner } from "../../../components/ui/Spinner";
import { StatusBadge } from "../../../components/ui/StatusBadge";
import { recommendationStatusColors } from "../../../lib/statusColors";
import {
  recommendationCategoryLabels,
  type RecommendationStatus,
} from "../api/recommendationsApi";
import { AIRecommendationReview } from "./AIRecommendationReview";
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

export function TripRecommendationsPanel({ tripId }: TripRecommendationsPanelProps) {
  const recommendations = useTripRecommendations(tripId);
  const accept = useAcceptRecommendation();
  const reject = useRejectRecommendation();
  const [filter, setFilter] = useState<RecommendationFilter>("all");

  const allRecommendations = recommendations.data?.results ?? [];
  const visibleRecommendations = useMemo(() => {
    if (filter === "all") return allRecommendations;
    return allRecommendations.filter((item) => item.status === filter);
  }, [allRecommendations, filter]);

  const aiRecommendations = visibleRecommendations.filter((item) => item.is_ai_generated);
  const manualRecommendations = visibleRecommendations.filter((item) => !item.is_ai_generated);

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

      {allRecommendations.length === 0 ? (
        <EmptyState message="No recommendations are available for this trip yet. AI-generated suggestions will appear here when the recommendation engine produces them." />
      ) : visibleRecommendations.length === 0 ? (
        <EmptyState message={`No ${filter} recommendations are available.`} />
      ) : (
        <div className="space-y-7">
          {aiRecommendations.length > 0 ? (
            <AIRecommendationReview
              recommendations={aiRecommendations}
              onAccept={handleAccept}
              onReject={handleReject}
              acceptPending={accept.isPending}
              rejectPending={reject.isPending}
              acceptRecommendationId={accept.variables?.recommendationId}
              rejectRecommendationId={reject.variables?.recommendationId}
              acceptError={accept.error instanceof Error ? accept.error : null}
              rejectError={reject.error instanceof Error ? reject.error : null}
            />
          ) : null}

          {manualRecommendations.length > 0 ? (
            <section aria-labelledby="manual-recommendations-heading">
              <div className="mb-4">
                <h3 id="manual-recommendations-heading" className="text-lg font-semibold">
                  Other recommendations
                </h3>
              </div>
              <ol className="space-y-4" aria-label="Other trip recommendations">
                {manualRecommendations.map((recommendation) => (
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
                              <span className="rounded-full bg-neutral-bg px-2 py-1 text-xs font-bold text-neutral">
                                {recommendationCategoryLabels[recommendation.category]}
                              </span>
                              <h4 className="mt-2 text-lg font-semibold">{recommendation.destination.name}</h4>
                              <p className="mt-1 text-sm text-neutral">
                                {recommendation.destination.city
                                  ? `${recommendation.destination.city}, ${recommendation.destination.country}`
                                  : recommendation.destination.country}
                              </p>
                            </div>
                            <div className="flex flex-col items-start gap-2 sm:items-end">
                              <StatusBadge status={recommendation.status} colorMap={recommendationStatusColors} />
                              <span className="text-sm font-semibold text-[var(--accent-dark)]">
                                {Math.round(Number(recommendation.score) * 100)}% match
                              </span>
                            </div>
                          </div>
                          <p className="mt-4 text-sm leading-6 text-neutral">{recommendation.reason}</p>
                        </div>
                      </div>
                    </Card>
                  </li>
                ))}
              </ol>
            </section>
          ) : null}
        </div>
      )}
    </section>
  );
}
