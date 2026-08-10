import { Navigate, Outlet } from "react-router-dom";
import { routes } from "./routeConfig";

export function ProtectedRoute() {
  const isAuthenticated = Boolean(localStorage.getItem("access_token"));
  return isAuthenticated ? <Outlet /> : <Navigate to={routes.public.login} replace />;
}