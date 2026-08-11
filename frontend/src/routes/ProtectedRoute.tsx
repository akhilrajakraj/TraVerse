import { Navigate, Outlet } from "react-router-dom";
import { Spinner } from "../components/ui/Spinner";
import { useAuth } from "../features/auth/hooks/useAuth";
import { routes } from "./routeConfig";

export function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <main className="auth-loading"><Spinner label="Checking your session…" /></main>;
  if (!isAuthenticated) return <Navigate to={routes.public.login} replace />;
  return <Outlet />;
}
