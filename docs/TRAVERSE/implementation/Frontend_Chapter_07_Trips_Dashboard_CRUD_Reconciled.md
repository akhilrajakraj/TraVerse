# Frontend Chapter 7 — Trips: Dashboard & Trip CRUD UI (Reconciled)

## Implementation status

Implemented against the current TraVerse repository on `main`.

**Backend changes: none.** The existing backend contract already supports the required list, create, retrieve, update, and delete endpoints. This chapter only needs list/create/retrieve on the frontend surface described by the supplied chapter, so no backend modification is justified.

## Reconciliation decisions

### 1. API paths follow the current `apiClient` contract

The frontend `apiRequest()` receives paths relative to the API origin. The actual backend is mounted at `/api/trips/`, so this chapter uses:

- `GET /api/trips/`
- `GET /api/trips/{uuid}/`
- `POST /api/trips/`

The supplied chapter's `/trips/` examples were reconciled to the repository's real URL structure.

### 2. The current trip list is an array, not a DRF paginated envelope

The current Django settings do not configure a global DRF pagination class, and `TripListCreateView` returns the authenticated user's queryset directly. The API layer therefore accepts both `Trip[]` and `PaginatedResponse<Trip>` and normalizes the current array response into the shared frontend list shape.

This follows the same boundary-normalization strategy established in Frontend Chapter 6 for destinations.

### 3. UUIDs are used end-to-end

`Trip` and `Destination` both use UUID primary keys in the backend. Therefore:

```ts
destination_ids: string[]
```

is used instead of the supplied chapter's `number[]`.

### 4. `Trip` matches the current serializer

The frontend model follows the current `TripSerializer` fields:

- `id`
- `title`
- `start_date`
- `end_date`
- `duration_days`
- `status`
- `traveler_count`
- `notes`
- `computed_budget_total`
- `destinations`
- `created_at`
- `updated_at`

`destination_ids` is write-only in the backend and therefore belongs only to `CreateTripPayload`.

### 5. Status remains read-only

The frontend does not send `status` when creating a trip and provides no direct status-editing control. The backend serializer marks `status` read-only and the dedicated `/status/` endpoint owns lifecycle transitions. The frontend only renders `StatusBadge` using the existing `tripStatusColors` mapping.

### 6. Dashboard architecture follows the current workspace shell

The supplied chapter expects a new `features/trips/pages/DashboardPage.tsx`. The current frontend already has a protected `/dashboard` route rendering `features/workspace/views/DashboardView.tsx`. Creating a second dashboard page would duplicate the existing route surface.

Therefore the existing `DashboardView` was upgraded to render the real trip dashboard while keeping the established `WorkspaceLayout` intact.

### 7. The missed create/detail routes are added to the real App location

The current application entry point is `src/app/App.tsx`, not the supplied chapter's `src/App.tsx` path. The following protected routes were added:

- `/trips/new`
- `/trips/:tripId`

Both remain inside `ProtectedRoute` and `WorkspaceLayout`, preserving authentication and the existing workspace UI.

### 8. DestinationPicker composes Chapter 6

`DestinationPicker` imports and reuses `useDestinationSearch` from the destinations feature. It adds selection/removal state without creating another debounce, API client, or destination search implementation.

The current Chapter 6 hook loads the catalog once and filters it client-side, so the picker naturally benefits from the same cached catalog.

### 9. Detail subsection links are intentionally represented as future surfaces

The supplied chapter assumes itinerary, budget, recommendations, and chat frontend routes already exist. In the current repository those routes are not yet present in `routeConfig.ts`, so creating dead links would be misleading.

The trip detail page therefore renders a clear “Coming next” shell for those domains. The actual links can be wired when their feature chapters are implemented.

### 10. “CRUD” is interpreted according to the supplied implementation

The supplied chapter's concrete code implements list/create/retrieve UI; it does not provide update/delete hooks or pages. Those operations are therefore not invented here. The backend's existing update/delete capability remains untouched and can be consumed by a later chapter if required.

## Backend contract verified before implementation

The current backend was read before changing the frontend:

- `apps.trips.models.Trip` uses UUID identity and the lifecycle states `draft`, `planning`, `planned`, `completed`, `cancelled`.
- `TripSerializer` exposes destinations read-only and accepts `destination_ids` for writes.
- `TripSerializer.status` is read-only.
- `TripListCreateView` scopes list/create operations to the authenticated user.
- `TripRetrieveUpdateDestroyView` scopes detail operations to the authenticated owner.
- `apps.trips.urls` exposes list, detail, status, and packing endpoints.
- `config.urls` mounts the trip API at `/api/trips/`.

No backend file was changed for this chapter.

## Implemented frontend surface

```text
frontend/src/features/trips/
├── api/tripsApi.ts
├── hooks/
│   ├── useTrips.ts
│   ├── useTrip.ts
│   └── useCreateTrip.ts
├── components/
│   ├── TripCard.tsx
│   └── DestinationPicker.tsx
├── pages/
│   ├── CreateTripPage.tsx
│   └── TripDetailPage.tsx
└── __tests__/
    ├── useTrips.test.tsx
    ├── useTrip.test.tsx
    ├── DestinationPicker.test.tsx
    └── CreateTripPage.test.tsx
```

Existing files reconciled:

- `frontend/src/features/workspace/views/DashboardView.tsx`
- `frontend/src/routes/routeConfig.ts`
- `frontend/src/app/App.tsx`

## Safety properties

- No frontend status mutation endpoint exists.
- No backend model, serializer, view, URL, migration, or settings file was changed.
- Authenticated API access continues through the shared `apiRequest()` JWT/refresh mechanism.
- Trip detail queries are disabled until a real UUID route parameter exists.
- Trip creation validates the date relationship locally before sending a request.
- Successful creation invalidates the trip-list query and navigates to the newly created trip.
- Destination selection prevents duplicate destinations and clears its search input after selection.

## Verification to run locally

From `frontend/`:

```bash
npm run test -- src/features/trips
npm run build
```

Then with the backend running and an authenticated account:

```text
/dashboard
/trips/new
/trips/<real-trip-uuid>
```

## Acceptance criteria

- [x] Real authenticated trip list replaces the dashboard placeholder.
- [x] Empty dashboard has a clear first-trip action.
- [x] Trip cards display real status using `StatusBadge` and `tripStatusColors`.
- [x] Create-trip form sends only backend-supported writable fields.
- [x] Destination picker reuses Chapter 6 search infrastructure.
- [x] UUID destination IDs are used.
- [x] Trip creation navigates to the created trip.
- [x] Trip detail displays real trip data.
- [x] Status has no editable UI.
- [x] `/trips/new` and `/trips/:tripId` are protected workspace routes.
- [x] Backend remains unchanged.
- [x] Regression tests were added for list, detail query guarding, destination selection, and creation validation.

> This reconciled chapter is the authoritative implementation guide for the current TraVerse frontend. Future frontend chapters should first verify the live backend contract and current frontend architecture before applying their source chapter literally.
