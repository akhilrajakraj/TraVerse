import { Link } from "react-router-dom";
import { routes } from "../../../routes/routeConfig";

export function PlannerView() {
  return (
    <div className="workspace-view">
      <section className="workspace-page-card">
        <span className="section-kicker">AI-powered planning</span>
        <h1>Plan your next journey.</h1>
        <p>The planner surface is protected and ready for its dedicated feature implementation. Your profile preferences will become inputs to the planning engine in the upcoming planner chapters.</p>
        <Link className="workspace-text-link" to={routes.protected.profile}>Review your profile →</Link>
      </section>
    </div>
  );
}
