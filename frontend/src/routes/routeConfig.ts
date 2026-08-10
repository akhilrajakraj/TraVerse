export const routes = {
  public: {
    landing: "/",
    login: "/login",
    register: "/register",
    sharedItinerary: "/share/:token",
  },
  protected: {
    dashboard: "/dashboard",
    createTrip: "/trips/new",
    tripDetail: "/trips/:tripId",
    itinerary: "/trips/:tripId/itinerary",
    budget: "/trips/:tripId/budget",
    recommendations: "/trips/:tripId/recommendations",
    packing: "/trips/:tripId/packing",
    chat: "/trips/:tripId/chat",
    profile: "/profile",
    settings: "/settings",
    bookings: "/trips/:tripId/bookings",
    analyticsAdmin: "/admin/analytics",
  },
} as const;