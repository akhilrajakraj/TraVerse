import { useMemo, useState, type FormEvent } from "react";

import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { EmptyState } from "../../../components/ui/EmptyState";
import { ErrorState } from "../../../components/ui/ErrorState";
import { Input } from "../../../components/ui/Input";
import { Spinner } from "../../../components/ui/Spinner";
import {
  budgetCategoryLabels,
  type BudgetCategory,
  type BudgetLineItem,
} from "../api/budgetApi";
import { useCreateBudgetLineItem } from "../hooks/useCreateBudgetLineItem";
import { useTripBudget } from "../hooks/useTripBudget";

interface TripBudgetPanelProps {
  tripId: string;
}

const budgetCategories = Object.entries(budgetCategoryLabels) as Array<
  [BudgetCategory, string]
>;

function formatMoney(
  amount: string | null | undefined,
  currency: string,
) {
  if (amount == null || amount === "") return "Not set";

  const numericAmount = Number(amount);
  if (Number.isNaN(numericAmount)) return `${currency} ${amount}`;

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
  }).format(numericAmount);
}

function sumCategory(items: BudgetLineItem[], category: BudgetCategory) {
  return items
    .filter((item) => item.category === category)
    .reduce((total, item) => total + (Number(item.amount) || 0), 0);
}

export function TripBudgetPanel({ tripId }: TripBudgetPanelProps) {
  const budget = useTripBudget(tripId);
  const createLineItem = useCreateBudgetLineItem();
  const [category, setCategory] = useState<BudgetCategory>("food");
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [validationError, setValidationError] = useState("");

  const categoryTotals = useMemo(() => {
    const items = budget.data?.line_items ?? [];

    return budgetCategories
      .map(([value, label]) => ({
        value,
        label,
        total: sumCategory(items, value),
      }))
      .filter((entry) => entry.total > 0);
  }, [budget.data?.line_items]);

  function resetForm() {
    setCategory("food");
    setDescription("");
    setAmount("");
    setValidationError("");
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedDescription = description.trim();
    const numericAmount = Number(amount);

    if (!trimmedDescription) {
      setValidationError("Description is required.");
      return;
    }

    if (
      !amount ||
      Number.isNaN(numericAmount) ||
      numericAmount < 0
    ) {
      setValidationError("Amount must be zero or greater.");
      return;
    }

    setValidationError("");
    createLineItem.mutate(
      {
        tripId,
        payload: {
          category,
          description: trimmedDescription,
          amount,
        },
      },
      { onSuccess: resetForm },
    );
  }

  if (budget.isLoading) {
    return <Spinner label="Loading budget..." />;
  }

  if (budget.isError || !budget.data) {
    return (
      <ErrorState
        title="Budget unavailable"
        message={
          budget.error instanceof Error
            ? budget.error.message
            : "We couldn't load this trip budget."
        }
        onRetry={() => void budget.refetch()}
      />
    );
  }

  const lineItems = budget.data.line_items;

  return (
    <section
      className="mt-8 border-t border-[var(--line)] pt-6"
      aria-labelledby="budget-heading"
    >
      <div className="mb-5">
        <span className="section-kicker">Budget</span>
        <h2 id="budget-heading" className="mt-1 text-xl font-semibold">
          Cost planning
        </h2>
        <p className="mt-2 text-sm text-neutral">
          Track trip costs with the budget automatically created for this trip.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="p-4">
          <span className="text-xs font-bold uppercase tracking-wide text-neutral">
            Computed total
          </span>
          <strong className="mt-2 block text-2xl">
            {formatMoney(budget.data.computed_total, budget.data.currency)}
          </strong>
        </Card>
        <Card className="p-4">
          <span className="text-xs font-bold uppercase tracking-wide text-neutral">
            Planned total
          </span>
          <strong className="mt-2 block text-2xl">
            {formatMoney(budget.data.planned_total, budget.data.currency)}
          </strong>
        </Card>
        <Card className="p-4">
          <span className="text-xs font-bold uppercase tracking-wide text-neutral">
            Line items
          </span>
          <strong className="mt-2 block text-2xl">{lineItems.length}</strong>
        </Card>
      </div>

      {categoryTotals.length > 0 ? (
        <div
          className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3"
          aria-label="Budget category totals"
        >
          {categoryTotals.map((entry) => (
            <Card key={entry.value} className="p-4">
              <span className="text-xs font-bold uppercase tracking-wide text-neutral">
                {entry.label}
              </span>
              <strong className="mt-2 block text-lg">
                {formatMoney(
                  entry.total.toFixed(2),
                  budget.data.currency,
                )}
              </strong>
            </Card>
          ))}
        </div>
      ) : null}

      <div className="mt-5 grid gap-5 lg:grid-cols-[1fr_320px]">
        <div>
          {lineItems.length > 0 ? (
            <ol className="space-y-3" aria-label="Budget line items">
              {lineItems.map((item) => (
                <li key={item.id}>
                  <Card className="p-4">
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="rounded-full bg-neutral-bg px-2 py-1 text-xs font-bold text-neutral">
                            {budgetCategoryLabels[item.category]}
                          </span>
                          {item.is_ai_estimated ? (
                            <span className="rounded-full bg-info/10 px-2 py-1 text-xs font-bold text-info">
                              AI estimate
                            </span>
                          ) : null}
                        </div>
                        <h3 className="mt-2 font-semibold">
                          {item.description}
                        </h3>
                      </div>
                      <strong className="text-lg">
                        {formatMoney(item.amount, budget.data.currency)}
                      </strong>
                    </div>
                  </Card>
                </li>
              ))}
            </ol>
          ) : (
            <EmptyState message="No budget line items yet. Add your first expected cost to start tracking this trip budget." />
          )}
        </div>

        <Card className="p-4">
          <form className="space-y-3" onSubmit={handleSubmit}>
            <h3 className="font-semibold">Add budget item</h3>

            <label
              className="flex flex-col gap-1.5 text-sm font-medium text-[var(--text)]"
              htmlFor="budget-category"
            >
              <span>Category</span>
              <select
                id="budget-category"
                className="rounded-xl border border-[var(--line)] bg-[var(--surface-solid)] px-3 py-3 text-[var(--text)] outline-none transition focus:border-orange-500 focus:ring-2 focus:ring-orange-500/20"
                value={category}
                onChange={(event) =>
                  setCategory(event.target.value as BudgetCategory)
                }
              >
                {budgetCategories.map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>

            <Input
              label="Description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
            <Input
              label="Amount"
              type="number"
              min="0"
              step="0.01"
              value={amount}
              onChange={(event) => setAmount(event.target.value)}
            />

            {validationError ? (
              <p className="text-sm text-red-600" role="alert">
                {validationError}
              </p>
            ) : null}

            {createLineItem.isError ? (
              <p className="text-sm text-red-600" role="alert">
                {createLineItem.error instanceof Error
                  ? createLineItem.error.message
                  : "Unable to add this budget item."}
              </p>
            ) : null}

            <Button type="submit" isLoading={createLineItem.isPending}>
              Add budget item
            </Button>
          </form>
        </Card>
      </div>
    </section>
  );
}
