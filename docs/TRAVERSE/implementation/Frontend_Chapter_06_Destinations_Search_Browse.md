# Frontend Chapter 6 — Destinations: Search & Browse UI (Reconciled)

**Volume 2: Identity & Core UI | Frontend Chapter 6 of 29**

> Reconciled against the current TraVerse repository. This chapter preserves the original goal—debounced search, reusable list typing, and the `api → hooks → pages` pattern—but follows the backend contract that actually exists today. The backend is read-only for this chapter.

## 1. Reconciliation Summary

The original chapter assumed a paginated, server-side search endpoint and a destination contract containing `destination_type`, `description`, and `average_daily_cost_usd`. The current repository does not expose that contract.

The current backend destination API is a `ListCreateAPIView` over active destinations and its serializer exposes:

- `id`
- `name`
- `country`
- `city`
- `latitude`
- `longitude`
- `image_url`
- `is_active`
- `created_at`
- `updated_at`

The backend destination view does not define pagination or a search filter. Therefore the frontend deliberately fetches the active catalog once and performs search filtering locally. This avoids changing the backend API and keeps the existing contract stable.

## 2. Architecture Decision

The feature keeps the established structure:

```text
DestinationsPage
      ↓
useDestinationSearch
      ↓
destinationsApi
      ↓
apiClient
      ↓
/api/destinations/
```

Shared infrastructure remains project-wide:

```text
src/hooks/useDebounce.ts
src/hooks/__tests__/useDebounce.test.ts
src/lib/types.ts
```

The destination feature remains:

```text
src/features/destinations/
├── api/destinationsApi.ts
├── hooks/useDestinationSearch.ts
├── components/DestinationCard.tsx
├── pages/DestinationsPage.tsx
└── __tests__/
    ├── useDestinationSearch.test.tsx
    └── DestinationsPage.test.tsx
```

## 3. Important Difference From the Original Chapter

The original design proposed:

```typescript
queryKey: ["destinations", "search", debouncedTerm]
queryFn: () => searchDestinations(debouncedTerm)
```

That is not appropriate for the current backend because there is no server-side search contract to call.

The reconciled implementation uses:

```typescript
queryKey: ["destinations", "catalog"]
queryFn: getDestinations
```

and filters the returned catalog locally using the debounced term.

This still gives:

- one backend request for the active catalog
- no request per keystroke
- 400ms debounce before filtering changes
- instant switching between terms after the catalog is loaded
- stable backend API usage
- a single cache entry for the catalog

The benefit is different from per-search-term server caching: returning to a previous term requires no network request because all search terms operate on the already cached catalog.

## 4. Shared `useDebounce`

`src/hooks/useDebounce.ts` remains generic and project-wide:

```typescript
export function useDebounce<T>(value: T, delayMs: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);

  return debouncedValue;
}
```

The cleanup is essential: every new input value cancels the previous pending timer.

## 5. Shared `PaginatedResponse<T>`

`src/lib/types.ts` still contains the reusable list envelope:

```typescript
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
```

This type remains useful throughout the frontend architecture even though the current destination endpoint does not require the backend to return this envelope. The destination API layer normalizes the raw catalog response when necessary, so the rest of the feature can continue using one stable frontend shape.

## 6. Destination API Contract

The current destination type mirrors the serializer exposed by the backend:

```typescript
export interface Destination {
  id: string;
  name: string;
  country: string;
  city: string;
  latitude: string;
  longitude: string;
  image_url: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
```

The API boundary accepts either a catalog array or the shared paginated envelope and normalizes an array into `{ count, next, previous, results }`.

This is intentionally a frontend-only compatibility boundary. No backend model, serializer, view, pagination setting, or route is changed.

## 7. Search Hook

The reconciled hook always enables the catalog query, including for an empty search term:

```typescript
const query = useQuery({
  queryKey: ["destinations", "catalog"],
  queryFn: getDestinations,
  staleTime: 5 * 60 * 1000,
});
```

This is important because an empty search means **browse the catalog**. Disabling the query for an empty string would produce a blank initial page.

After the catalog is loaded, the debounced term is matched against:

```text
name
country
city
```

The returned `data` keeps the existing shared shape while replacing `results` and `count` with the filtered values.

## 8. Destination Card

`DestinationCard` follows the existing shared `Card` component and the current visual language. It displays:

- destination image when `image_url` exists
- a neutral visual fallback when no image exists
- destination name
- `city, country`
- an `Explore` label

The card does not invent fields that are absent from the current serializer.

## 9. Page Behavior

`DestinationsPage` owns only the raw input state:

```typescript
const [searchTerm, setSearchTerm] = useState("");
```

Debouncing and catalog querying remain hidden inside `useDestinationSearch`.

The page renders four explicit states:

1. initial/loading state
2. error state with retry
3. zero-result `EmptyState`
4. destination card grid

It also distinguishes initial loading from background fetching so a cached catalog is not replaced by a full-page loading state during subsequent query work.

## 10. Why This Fix Matters

The original implementation had a subtle architectural mismatch: the hook disabled the query when the search term was empty:

```typescript
enabled: debouncedTerm.length > 0
```

That prevented the catalog from loading when the Destinations page was first opened. The reconciled implementation removes that condition.

The correct rule for the current architecture is:

```text
empty search = browse all active destinations
non-empty search = filter the cached active catalog
```

## 11. Testing Requirements

The feature now verifies:

### `useDebounce`

- value does not update before the delay
- a new value resets the timer
- value updates after the final 400ms window

### `useDestinationSearch`

- the shared catalog is fetched once
- changing search terms filters the shared catalog
- revisiting a previous term does not trigger another catalog request

### `DestinationsPage`

- the catalog renders without typing a search term
- zero results show `EmptyState`
- matching destinations render correctly

The initial-catalog test is especially important because it protects against the blank-page regression caused by disabling the query for an empty term.

## 12. Verification

Run from `frontend/`:

```bash
npm run test
npm run build
```

For Docker development from the repository root:

```powershell
docker compose -f infrastructure/compose/docker-compose.yml -f infrastructure/compose/docker-compose.dev.yml up --build
```

Then verify:

```text
http://localhost:5173/destinations
```

Manual acceptance:

- page opens with destinations visible
- typing remains instant
- filtering starts after approximately 400ms of inactivity
- searching by name works
- searching by city works
- searching by country works
- unknown terms show the empty state
- clearing the search returns the full catalog
- backend remains untouched

## 13. Backend Safety Decision

**Backend modification: rejected.**

The current backend already exposes the required read-only destination catalog and the application log confirms `GET /api/destinations/` succeeds with HTTP 200. Adding backend search or pagination would change a shared API contract and could affect future consumers. The frontend can satisfy the current chapter without that risk.

## 14. Implementation Checklist

- [x] Generic `useDebounce<T>` remains project-wide
- [x] Shared `PaginatedResponse<T>` remains in `src/lib/types.ts`
- [x] Destination API remains isolated in `api/`
- [x] Search logic remains isolated in `useDestinationSearch`
- [x] Empty search loads the catalog
- [x] Search is client-side against the existing backend contract
- [x] Destination fields match the current serializer
- [x] Zero results render `EmptyState`
- [x] Initial catalog rendering is covered by a regression test
- [x] Backend remains unchanged

## 15. Result

Frontend Chapter 6 is now implemented as a **read-only destination catalog feature that fits the actual TraVerse architecture**, rather than forcing the repository to match an outdated server-search/pagination assumption.

The chapter's core architectural lesson remains intact: shared mechanisms belong in shared locations, API details stay in the API layer, query behavior stays in hooks, and pages remain focused on UI state and presentation.
