import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  createBudgetLineItem,
  type CreateBudgetLineItemPayload,
} from "../api/budgetApi";
import { tripBudgetQueryKey } from "./useTripBudget";

interface CreateBudgetLineItemVariables {
  tripId: string;
  payload: CreateBudgetLineItemPayload;
}

export function useCreateBudgetLineItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tripId, payload }: CreateBudgetLineItemVariables) =>
      createBudgetLineItem(tripId, payload),
    onSuccess: (_lineItem, variables) => {
      queryClient.invalidateQueries({
        queryKey: tripBudgetQueryKey(variables.tripId),
      });
    },
  });
}
