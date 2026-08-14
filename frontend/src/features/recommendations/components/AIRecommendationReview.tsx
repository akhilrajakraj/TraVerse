import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { StatusBadge } from "../../../components/ui/StatusBadge";
import { recommendationCategoryLabels } from "../api/recommendationsApi";
import type { Recommendation, RecommendationStatus } from "../api/recommendationsApi";
import { recommendationStatusColors } from "../../../lib/statusColors";

interface AIRecommendationReviewProps {
  recommendations: Recommendation[];
  onAccept: (recommendationId: string) => void;
  onReject: (recommendationId: string) => void;
  acceptPending: boolean;
  rejectPending: boolean;
  acceptRecommendationId?: string;
  rejectRecommendationId?: string;
  acceptError?: Error | null;
  rejectError?: Error | null;
}

function formatScore(score: string) {
  const numericScore = Number(score);
  if (Number.isNaN(numericScore)) return score;
  return `${Math.round(numericScore * 100)}% match`;
}

function getDestinationLabel(recommendation: Recommendation) {
  const { city, country } = recommendation.destination;
  return city ? `${city}, ${country}` : country;
}

function sortByScore(recommendations: Recommendation[]) {
  return [...recommendations].sort((left, right) => {
    const leftScore = Number(left.score);
    const rightScore = Number(right.score);

    if (Number.isNaN(leftScore) || Number.isNaN(rightScore)) return 0;
    return rightScore - leftScore;
  });
}

export function AIRecommendationReview({
  recommendations,
  onAccept,
  onReject,
  acceptPending,
  rejectPending,
  acceptRecommendationId,
  rejectRecommendationId,
  acceptError,
  rejectError,
}: AIRecommendationReviewProps) {
  const orderedRecommendations = sortByScore(recommendations);

  if (orderedRecommendations.length === 0) return null;

  return (
    <section aria-labelledby="ai-recommendation-review-heading">
      <div className="mb-4">
        <span className="section-kicker">AI recommendations</span>
        <h3 id="ai-recommendation-review-heading" className="mt-1 text-lg font-semibold">
          Review AI suggestions
        </h3>
        <p className="mt-2 text-sm text-neutral">
          Suggestions are ordered by the recommendation score returned by the backend. Keep or dismiss each pending suggestion based on your trip.
        </p>
      </div>

      <ol className="space-y-4" aria-label="AI recommendation review">
        {orderedRecommendations.map((recommendation) => {
          const isAccepting = acceptPending && acceptRecommendationId === recommendation.id;
          const isRejecting = rejectPending && rejectRecommendationId === recommendation.id;
          const isMutating = acceptPending || rejectPending;

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
                          <span className="rounded-full bg-info/10 px-2 py-1 text-xs font-bold text-info">
                            AI recommendation
                          </span>
                        </div>
                        <h4 className="mt-2 text-lg font-semibold">
                          {recommendation.destination.name}
                        </h4>
                        <p className="mt-1 text-sm text-neutral">
                          {getDestinationLabel(recommendation)}
                        </p>
                      </div>

                      <div className="flex flex-col items-start gap-2 sm:items-end">
                        <StatusBadge
                          status={recommendation.status as RecommendationStatus}
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
                          onClick={() => onAccept(recommendation.id)}
                          isLoading={isAccepting}
                          disabled={isMutating && !isAccepting}
                        >
                          Keep recommendation
                        </Button>
                        <Button
                          type="button"
                          variant="danger"
                          onClick={() => onReject(recommendation.id)}
                          isLoading={isRejecting}
                          disabled={isMutating && !isRejecting}
                        >
                          Dismiss
                        </Button>
                      </div>
                    ) : null}

                    {acceptError && acceptRecommendationId === recommendation.id ? (
                      <p className="mt-3 text-sm text-red-600" role="alert">
                        {acceptError.message || "Unable to accept this recommendation."}
                      </p>
                    ) : null}
                    {rejectError && rejectRecommendationId === recommendation.id ? (
                      <p className="mt-3 text-sm text-red-600" role="alert">
                        {rejectError.message || "Unable to dismiss this recommendation."}
                      </p>
                    ) : null}
                  </div>
                </div>
              </Card>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
