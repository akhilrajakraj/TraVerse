/**
 * Standard Django REST Framework page-number pagination envelope.
 * Shared by all future list-rendering features.
 */
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
