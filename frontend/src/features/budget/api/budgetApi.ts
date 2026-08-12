import { apiRequest } from "../../../lib/apiClient";

export type BudgetCategory =
  | "accommodation"
  | "transport"
  | "food"
  | "activities"
  | "shopping"
  | "misc";

export interface BudgetLineItem {
  id: string;
  category: BudgetCategory;
  description: string;
  amount: string;
  is_ai_estimated: boolean;
  created_at: string;
}

export interface TripBudget {
  id: string;
  currency: string;
  planned_total: string | null;
  computed_total: string;
  line_items: BudgetLineItem[];
}

export interface CreateBudgetLineItemPayload {
  category: BudgetCategory;
  description: string;
  amount: string;
}

export const budgetCategoryLabels: Record<BudgetCategory, string> = {
  accommodation: "Accommodation",
  transport: "Transport",
  food: "Food & dining",
  activities: "Activities & tours",
  shopping: "Shopping",
  misc: "Miscellaneous",
};

export function fetchTripBudget(tripId: string): Promise<TripBudget> {
  return apiRequest<TripBudget>(`/api/budget/trips/${tripId}/budget/`);
}

export function createBudgetLineItem(
  tripId: string,
  payload: CreateBudgetLineItemPayload,
): Promise<BudgetLineItem> {
  return apiRequest<BudgetLineItem>(
    `/api/budget/trips/${tripId}/budget/items/`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}
