import { useMemo, useState } from "react";
import { ArrowRight, CalendarDays, Check, Compass, Menu, Search, Sparkles, X } from "lucide-react";
import Compass3D from "../components/Compass3D";
import BackgroundShader from "../components/BackgroundShader";

const interests = ["Food & Culture", "Nature", "History", "Nightlife"];

export function HomePage() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [destination, setDestination] = useState("");
  const [startDate, setStartDate] = useState("");
  const [duration, setDuration] = useState("7");
  const [style, setStyle] = useState("balanced");
  const [pace, setPace] = useState("moderate");
  const [selectedInterests, setSelectedInterests] = useState(["Food & Culture", "Nature"]);
  const [generated, setGenerated] = useState(false);

  const destinationLabel = useMemo(() => destination.trim() || "your next destination", [destination]);

  function toggleInterest(interest: string) {
    setSelectedInterests((current) => current.includes(interest) ? current.filter((item) => item !== interest) : [...current, interest]);
  }

  function scrollToPlanner() {
    document.getElementById("planner")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function generateItinerary(event: React.FormEvent) {
    event.preventDefault();
    setGenerated(true);
  }

  return (
    <div className="home-page">
      <header className="site-header">
        <a className="brand" href="/" aria-label="TraVerse home">
          <span className="brand-mark"><Compass size={21} /></span>
          <span>TraVerse</span>
        </a>
        <nav className="desktop-nav" aria-label="Primary navigation">
          <a className="active" href="#discover">Discover</a>
          <a href="#planner">Itineraries</a>
          <a href="#discover">Hotels</a>
          <a href="#discover">Flights</a>
        </nav>
        <button className="plan-button" type="button" onClick={scrollToPlanner}><Compass size={18} /> Plan Trip</button>
        <button className="menu-button" type="button" onClick={() => setMenuOpen((open) => !open)} aria-label="Toggle navigation" aria-expanded={menuOpen}>
          {menuOpen ? <X /> : <Menu />}
        </button>
        {menuOpen && <nav className="mobile-nav"><a href="#discover" onClick={() => setMenuOpen(false)}>Discover</a><a href="#planner" onClick={() => setMenuOpen(false)}>Itineraries</a><a href="#discover" onClick={() => setMenuOpen(false)}>Hotels</a><a href="#discover" onClick={() => setMenuOpen(false)}>Flights</a></nav>}
      </header>

      <main>
        <section id="discover" className="hero">
          <BackgroundShader />
          <div className="hero-wash" />
          <div className="hero-content">
            <div className="hero-copy">
              <p className="eyebrow"><Sparkles size={15} /> AI-powered travel planning</p>
              <h1>Where will your next journey take you?</h1>
              <p className="hero-description">I'm your expert AI itinerary assistant. Tell me a bit about your dream trip, and I'll handle the rest.</p>
              <div className="search-box">
                <Search className="search-icon" size={21} />
                <input value={destination} onChange={(event) => setDestination(event.target.value)} onKeyDown={(event) => event.key === "Enter" && scrollToPlanner()} placeholder="Search destinations, experiences, or vibes..." aria-label="Search destinations" />
                <button type="button" onClick={scrollToPlanner} aria-label="Start planning"><ArrowRight /></button>
              </div>
              <div className="hero-meta"><span>Personalized</span><span>•</span><span>Flexible</span><span>•</span><span>AI-assisted</span></div>
            </div>
            <div className="compass-stage" aria-hidden="true"><Compass3D /></div>
          </div>
        </section>

        <section id="planner" className="planner-section">
          <div className="section-heading">
            <p className="eyebrow dark"><Compass size={15} /> Your trip, your way</p>
            <h2>Let's personalize your adventure.</h2>
            <p>Fine-tune the details to create an itinerary that matches your style.</p>
          </div>

          <form onSubmit={generateItinerary}>
            <div className="preference-grid">
              <article className="preference-card">
                <div className="card-heading"><span className="icon-box"><CalendarDays /></span><h3>Dates &amp; Duration</h3></div>
                <label>Start Date<input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} /></label>
                <label>Duration (Days)<input min="1" type="number" value={duration} onChange={(event) => setDuration(event.target.value)} /></label>
              </article>

              <article className="preference-card">
                <div className="card-heading"><span className="icon-box orange"><Sparkles /></span><h3>Travel Style</h3></div>
                <div className="option-stack">
                  {["budget", "balanced", "luxury"].map((value) => <label className={`choice ${style === value ? "selected" : ""}`} key={value}><input type="radio" name="style" value={value} checked={style === value} onChange={(event) => setStyle(event.target.value)} /><span>{value === "budget" ? "Budget-friendly" : value[0].toUpperCase() + value.slice(1)}</span></label>)}
                </div>
              </article>

              <article className="preference-card">
                <div className="card-heading"><span className="icon-box"><Compass /></span><h3>Pace &amp; Focus</h3></div>
                <label>Pace</label>
                <div className="segmented">
                  {["relaxed", "moderate", "fast"].map((value) => <label key={value}><input type="radio" name="pace" value={value} checked={pace === value} onChange={(event) => setPace(event.target.value)} /><span>{value[0].toUpperCase() + value.slice(1)}</span></label>)}
                </div>
                <label>Interests</label>
                <div className="chips">{interests.map((interest) => <button className={`chip ${selectedInterests.includes(interest) ? "selected" : ""}`} key={interest} type="button" onClick={() => toggleInterest(interest)}>{selectedInterests.includes(interest) && <Check size={14} />}{interest}</button>)}</div>
              </article>
            </div>

            <div className="generate-area">
              <p className="destination-summary">Planning <strong>{destinationLabel}</strong> · {duration || "—"} days · {style} · {pace}</p>
              <button className="generate-button" type="submit"><Sparkles size={19} /> Generate My Itinerary <ArrowRight size={19} /></button>
              {generated && <p className="success-note" role="status">Your preferences are ready. The AI itinerary workflow will connect here in the next feature chapter.</p>}
            </div>
          </form>
        </section>
      </main>

      <footer className="site-footer">
        <div><div className="footer-brand">TraVerse</div><p>Your intelligent travel co-pilot for seamless trip planning and routing.</p></div>
        <nav><a href="#discover">About</a><a href="#planner">Plan</a><a href="#discover">Safety</a><a href="#discover">Privacy</a></nav>
      </footer>
    </div>
  );
}