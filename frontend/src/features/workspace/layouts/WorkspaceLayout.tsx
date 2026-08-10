import { useState } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/hooks/useAuth";
import { useTheme } from "../../theme/ThemeProvider";
import { routes } from "../../../routes/routeConfig";

const navItems = [
  { label: "Dashboard", path: routes.protected.dashboard, icon: "⌂" },
  { label: "AI Planner", path: routes.protected.planner, icon: "✦", badge: "AI" },
  { label: "Profile", path: routes.protected.profile, icon: "◉" },
  { label: "Saved Trips", path: routes.protected.saved, icon: "◇" },
  { label: "Settings", path: routes.protected.settings, icon: "⚙" },
] as const;

export function WorkspaceLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate(routes.public.login, { replace: true });
  }

  return (
    <div className="workspace-shell">
      {mobileOpen && <button className="workspace-overlay" aria-label="Close navigation" onClick={() => setMobileOpen(false)} />}

      <aside className={`workspace-sidebar ${collapsed ? "collapsed" : ""} ${mobileOpen ? "mobile-open" : ""}`}>
        <div>
          <div className="workspace-brand-row">
            <Link to={routes.public.home} className="workspace-brand">
              <span className="brand-mark">T</span>
              {!collapsed && <span>TraVerse</span>}
            </Link>
            <button className="workspace-collapse" onClick={() => setCollapsed((value) => !value)} aria-label="Toggle sidebar">
              {collapsed ? "→" : "←"}
            </button>
          </div>

          <nav className="workspace-nav" aria-label="Workspace navigation">
            {navItems.map((item) => (
              <NavLink key={item.path} to={item.path} onClick={() => setMobileOpen(false)} className={({ isActive }) => `workspace-nav-item ${isActive ? "active" : ""}`}>
                <span className="workspace-nav-icon">{item.icon}</span>
                {!collapsed && (
                  <>
                    <span>{item.label}</span>
                    {"badge" in item && item.badge ? <small>{item.badge}</small> : null}
                  </>
                )}
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="workspace-sidebar-bottom">
          <button className="workspace-utility" onClick={toggleTheme}>{theme === "dark" ? "☀" : "☾"}{!collapsed && <span>{theme === "dark" ? "Light mode" : "Dark mode"}</span>}</button>
          <div className="workspace-user">
            <span className="workspace-avatar">{user?.first_name?.charAt(0) ?? "T"}</span>
            {!collapsed && <div className="workspace-user-copy"><strong>{user?.first_name || "Traveler"}</strong><small>{user?.email || ""}</small></div>}
            {!collapsed && <button onClick={handleLogout} className="workspace-logout" aria-label="Log out">↗</button>}
          </div>
        </div>
      </aside>

      <div className="workspace-main">
        <header className="workspace-topbar">
          <button className="workspace-mobile-menu" onClick={() => setMobileOpen(true)} aria-label="Open navigation">☰</button>
          <Link to={routes.public.home}>Back to TraVerse ↗</Link>
        </header>
        <main className="workspace-content"><Outlet /></main>
      </div>
    </div>
  );
}
