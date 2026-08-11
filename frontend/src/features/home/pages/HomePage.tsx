import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Button } from "../../../components/ui/Button";
import { ThemeToggle } from "../../../components/ui/ThemeToggle";
import { verifyApiConnection } from "../../../lib/verifyApiConnection";
import { BackgroundShader } from "../components/BackgroundShader";
import { Compass3D } from "../components/Compass3D";

export function HomePage() {
  const [health, setHealth] = useState<"checking" | "healthy" | "offline">("checking");

  useEffect(() => {
    let active = true;
    verifyApiConnection()
      .then(() => active && setHealth("healthy"))
      .catch(() => active && setHealth("offline"));
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="home-page">
      <BackgroundShader />
      <header className="home-header">
        <Link to="/" className="brand" aria-label="TraVerse home">
          <span className="brand-mark">T</span>
          <span>TraVerse</span>
        </Link>
        <nav className="home-nav" aria-label="Primary navigation">
          <a className="active" href="#discover">Discover</a>
          <a href="#planner">Itineraries</a>
          <a href="#stays">Hotels</a>
          <a href="#flights">Flights</a>
        </nav>
        <div className="header-actions">
          <div className={`health-pill ${health}`} title="Backend connection status">
            <span className="health-dot" />
            {health === "checking" ? "Checking" : health === "healthy" ? "Ready" : "Offline"}
          </div>
          <ThemeToggle />
          <Link to="/login" className="header-login">Sign in</Link>
          <Link to="/planner"><Button className="plan-button">Plan a trip</Button></Link>
        </div>
      </header>

      <main>
        <section className="home-hero" id="discover">
          <div className="hero-copy reveal reveal-one">
            <span className="eyebrow-pill">AI-powered travel planning</span>
            <h1>Go somewhere<br /><em>worth remembering.</em></h1>
            <p className="hero-lead">
              Tell TraVerse what you want from your next journey. We turn your destination,
              pace, budget, and interests into a trip that feels made for you.
            </p>
            <div className="hero-search">
              <span aria-hidden="true">⌕</span>
              <input aria-label="Search travel ideas" placeholder="Search destinations, experiences, or vibes…" />
              <Link to="/planner" className="search-submit" aria-label="Start planning">→</Link>
            </div>
            <div className="hero-meta">
              <span>✦ Personalized itineraries</span>
              <span>◈ Smart budget planning</span>
              <span>◎ Human-friendly AI</span>
            </div>
          </div>
          <div className="hero-visual reveal reveal-two">
            <Compass3D />
          </div>
        </section>

        <section className="planner-section" id="planner">
          <div className="section-heading reveal">
            <span className="section-kicker">Your journey, your rules</span>
            <h2>Let's personalize your adventure.</h2>
            <p>Start with the details that shape a great trip. Everything else can evolve later.</p>
          </div>

          <div className="preference-grid">
            <article className="preference-card reveal reveal-one">
              <div className="preference-icon">◷</div>
              <div><span className="card-kicker">01 · Timing</span><h3>When are you going?</h3></div>
              <label>Start date<input type="date" /></label>
              <label>Duration<input min="1" placeholder="e.g. 7 days" type="number" /></label>
            </article>

            <article className="preference-card reveal reveal-two">
              <div className="preference-icon orange">✦</div>
              <div><span className="card-kicker">02 · Style</span><h3>How do you like to travel?</h3></div>
              <div className="choice-list">
                {[["budget", "Budget-friendly", "Keep costs intentional"], ["balanced", "Balanced", "A little of everything"], ["luxury", "Luxury", "Make it memorable"]].map(([value, title, detail], index) => (
                  <label className="choice" key={value}>
                    <input defaultChecked={index === 1} name="travel-style" type="radio" value={value} />
                    <span><strong>{title}</strong><small>{detail}</small></span>
                  </label>
                ))}
              </div>
            </article>

            <article className="preference-card reveal reveal-three">
              <div className="preference-icon blue">✧</div>
              <div><span className="card-kicker">03 · Pace</span><h3>What should the days feel like?</h3></div>
              <div className="pace-grid">
                <label><input defaultChecked name="pace" type="radio" /><span>Slow<br /><small>Unhurried</small></span></label>
                <label><input name="pace" type="radio" /><span>Balanced<br /><small>Flexible</small></span></label>
                <label><input name="pace" type="radio" /><span>Active<br /><small>Full days</small></span></label>
              </div>
              <label>What are you into?<input placeholder="Food, beaches, art, hiking…" /></label>
            </article>
          </div>

          <div className="planner-cta reveal">
            <div><span className="section-kicker">Ready when you are</span><h3>Turn a few ideas into a real journey.</h3></div>
            <Link to="/planner"><Button className="cta-button">Start planning <span>→</span></Button></Link>
          </div>
        </section>

        <section className="feature-strip" id="stays">
          <div><span>01</span><strong>Discover</strong><p>Find places that match your mood, not just a map.</p></div>
          <div><span>02</span><strong>Plan</strong><p>Build a practical itinerary around your real constraints.</p></div>
          <div><span>03</span><strong>Explore</strong><p>Keep every trip detail together, from flights to documents.</p></div>
        </section>
      </main>

      <footer className="home-footer" id="flights">
        <span>© {new Date().getFullYear()} TraVerse</span>
        <span>Travel farther. Plan smarter.</span>
      </footer>
    </div>
  );
}
