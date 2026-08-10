import { useEffect, useState } from "react";

const routes = ["/", "/login", "/register", "/destinations", "/trips"] as const;

type RoutePath = (typeof routes)[number];

function normalizePath(pathname: string): RoutePath {
  if (routes.includes(pathname as RoutePath)) return pathname as RoutePath;
  return "/";
}

function RouteView({ path }: { path: RoutePath }) {
  const labels: Record<RoutePath, string> = {
    "/": "TraVerse",
    "/login": "Login",
    "/register": "Register",
    "/destinations": "Destinations",
    "/trips": "Trips",
  };

  return (
    <main style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: "2rem" }}>
      <section style={{ maxWidth: 720, width: "100%" }}>
        <p style={{ letterSpacing: "0.08em", textTransform: "uppercase", fontWeight: 800 }}>TraVerse</p>
        <h1>{labels[path]}</h1>
        <p>Frontend architecture is ready for feature implementation.</p>
      </section>
    </main>
  );
}

export function Router() {
  const [path, setPath] = useState<RoutePath>(() => normalizePath(window.location.pathname));

  useEffect(() => {
    const onPopState = () => setPath(normalizePath(window.location.pathname));
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  return <RouteView path={path} />;
}
