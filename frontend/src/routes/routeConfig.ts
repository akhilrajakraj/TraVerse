export const routes = {
  public: { home: "/", login: "/login", register: "/register" },
  protected: { dashboard: "/dashboard", planner: "/planner" },
} as const;
