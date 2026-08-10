import { useEffect, useRef } from "react";

export default function BackgroundShader() {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const context = canvas.getContext("2d");
    if (!context) return;
    let frame = 0;
    const resize = () => { canvas.width = canvas.clientWidth * Math.min(window.devicePixelRatio, 2); canvas.height = canvas.clientHeight * Math.min(window.devicePixelRatio, 2); };
    const draw = (time: number) => {
      const w = canvas.width, h = canvas.height;
      const scale = Math.min(w, h) / 900;
      context.clearRect(0, 0, w, h);
      const x = w * (0.52 + Math.sin(time * 0.00018) * 0.08);
      const y = h * (0.45 + Math.cos(time * 0.00022) * 0.06);
      const gradient = context.createRadialGradient(x, y, 0, w * 0.5, h * 0.5, Math.max(w, h) * 0.65);
      gradient.addColorStop(0, "rgba(255, 150, 99, 0.34)");
      gradient.addColorStop(0.45, "rgba(255, 199, 145, 0.20)");
      gradient.addColorStop(1, "rgba(255, 255, 255, 0)");
      context.fillStyle = gradient;
      context.fillRect(0, 0, w, h);
      context.beginPath();
      context.arc(w * 0.77, h * 0.36, 190 * scale, 0, Math.PI * 2);
      context.fillStyle = "rgba(70, 141, 173, 0.12)";
      context.fill();
      frame = requestAnimationFrame(draw);
    };
    resize();
    window.addEventListener("resize", resize);
    frame = requestAnimationFrame(draw);
    return () => { cancelAnimationFrame(frame); window.removeEventListener("resize", resize); };
  }, []);
  return <canvas ref={ref} className="background-shader" aria-hidden="true" />;
}