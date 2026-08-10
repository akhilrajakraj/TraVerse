import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider } from "../features/auth/context/AuthContext";
import { LoginPage } from "../features/auth/pages/LoginPage";
import { RegisterPage } from "../features/auth/pages/RegisterPage";
import { HomePage } from "../features/home/pages/HomePage";
import { ProfilePage } from "../features/profile/pages/ProfilePage";
import { ThemeProvider } from "../features/theme/ThemeProvider";
import { DashboardView } from "../features/workspace/views/DashboardView";
import { PlannerView } from "../features/workspace/views/PlannerView";
import { WorkspaceLayout } from "../features/workspace/layouts/WorkspaceLayout";
import { queryClient } from "../lib/queryClient";
import { ProtectedRoute } from "../routes/ProtectedRoute";
import { routes } from "../routes/routeConfig";

function WorkspacePlaceholder({ title, description }: { title: string; description: string }) {
  return (
    <section className="workspace-placeholder">
      <span className="section-kicker">TraVerse workspace</span>
      <h1>{title}</h1>
      <p>{description}</p>
      <span className="workspace-placeholder-badge">Feature surface ready</span>
    </section>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <Routes>
              <Route path={routes.public.home} element={<HomePage />} />
              <Route path={routes.public.login} element={<LoginPage />} />
              <Route path={routes.public.register} element={<RegisterPage />} />
              <Route element={<ProtectedRoute />}>
                <Route element={<WorkspaceLayout />}>
                  <Route path={routes.protected.dashboard} element={<DashboardView />} />
                  <Route path={routes.protected.planner} element={<PlannerView />} />
                  <Route path={routes.protected.profile} element={<ProfilePage />} />
                  <Route path={routes.protected.saved} element={<WorkspacePlaceholder title="Saved trips" description="Your saved destinations and itineraries will appear here as those features are implemented." />} />
                  <Route path={routes.protected.settings} element={<WorkspacePlaceholder title="Settings" description="Account and application settings will live here as their feature chapters are implemented." />} />
                </Route>
              </Route>
              <Route path="*" element={<Navigate to={routes.public.home} replace />} />
            </Routes>
          </BrowserRouter>
        </QueryClientProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}
