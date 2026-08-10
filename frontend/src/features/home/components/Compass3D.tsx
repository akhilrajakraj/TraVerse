import { useEffect, useRef } from "react";

export function Compass3D() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const onMove = (event: MouseEvent) => {
      const rect = element.getBoundingClientRect();
      const x = ((event.clientX - rect.left) / rect.width - 0.5) * 2;
      const y = ((event.clientY - rect.top) / rect.height - 0.5) * 2;
      element.style.setProperty("--tilt-x", `${y * -8}deg`);
      element.style.setProperty("--tilt-y", `${x * 10}deg`);
    };

    const reset = () => {
      element.style.setProperty("--tilt-x", "0deg");
      element.style.setProperty("--tilt-y", "0deg");
    };

    window.addEventListener("mousemove", onMove);
    element.addEventListener("mouseleave", reset);
    return () => {
      window.removeEventListener("mousemove", onMove);
      element.removeEventListener("mouseleave", reset);
    };
  }, []);

  return (
    <div ref={ref} className="compass-stage" aria-label="Interactive travel compass" role="img">
      <div className="compass-glow" />
      <div className="compass">
        <div className="compass-ring" />
        <div className="compass-face">
          <span className="compass-mark north">N</span>
          <span className="compass-mark east">E</span>
          <span className="compass-mark south">S</span>
          <span className="compass-mark west">W</span>
          <div className="needle north-needle" />
          <div className="needle south-needle" />
          <div className="compass-center" />
        </div>
      </div>
      <div className="compass-orbit orbit-one" />
      <div className="compass-orbit orbit-two" />
    </div>
  );
}
