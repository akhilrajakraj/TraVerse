import { Link } from "react-router-dom";
import { useAuth } from "../../auth/hooks/useAuth";
import { routes } from "../../../routes/routeConfig";

export function DashboardView() {
  const { user } = useAuth();

  return (
    <div className="workspace-view">
      <section className="workspace-hero">
        <div>
          <span className="section-kicker">Your travel workspace</span>
          <h1>Welcome back{user?.first_name ? `, ${user.first_name}` : ""}.</h1>
          <p>Your next journey starts here. Build an itinerary, refine your preferences, and keep every important detail together.</p>
        </div>
        <Link to={routes.protected.planner} className="workspace-primary-action">Plan a trip <span>→</span></Link>
      </section>

      <section className="workspace-stat-grid">
        <article><span>01</span><strong>AI Planner</strong><p>Turn a destination and a few preferences into a structured trip.</p></article>
        <article><span>02</span><strong>Your Profile</strong><p>Keep the details that help TraVerse personalize future journeys.</p></article>
        <article><span>03</span><strong>Saved Trips</strong><p>A dedicated home for the itineraries and destinations you keep.</p></article>
      </section>
    </div>
  );
}
