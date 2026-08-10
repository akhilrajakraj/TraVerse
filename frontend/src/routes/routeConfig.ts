export const routes = {
  public: {
    home: "/",
    login: "/login",
    register: "/register",
  },
  protected: {
    dashboard: "/dashboard",
    planner: "/planner",
    profile: "/profile",
    saved: "/workspace/saved",
    settings: "/workspace/settings",
  },
} as const;
