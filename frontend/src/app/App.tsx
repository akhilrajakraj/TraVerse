import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { LoginPage } from "../features/auth/pages/LoginPage";
import { RegisterPage } from "../features/auth/pages/RegisterPage";
import { HomePage } from "../features/home/pages/HomePage";
import { ThemeProvider } from "../features/theme/ThemeProvider";
import { ProtectedRoute } from "../routes/ProtectedRoute";
import { routes } from "../routes/routeConfig";

function WorkspacePage({ title }: { title: string }) {
  return <main className="workspace-page"><span className="section-kicker">TraVerse workspace</span><h1>{title}</h1><p>This protected surface is wired and ready for its feature chapter.</p><a href={routes.public.home}>Return home</a></main>;
}

export default function App() {
  return <ThemeProvider><BrowserRouter><Routes>
    <Route path={routes.public.home} element={<HomePage />} />
    <Route path={routes.public.login} element={<LoginPage />} />
    <Route path={routes.public.register} element={<RegisterPage />} />
    <Route element={<ProtectedRoute />}>
      <Route path={routes.protected.dashboard} element={<WorkspacePage title="Your travel workspace" />} />
      <Route path={routes.protected.planner} element={<WorkspacePage title="AI trip planner" />} />
    </Route>
    <Route path="*" element={<Navigate to={routes.public.home} replace />} />
  </Routes></BrowserRouter></ThemeProvider>;
}
