import { useEffect, useRef } from "react";

export function BackgroundShader() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const context = canvas.getContext("2d");
    if (!context) return;

    let frame = 0;
    let animationId = 0;
    let width = 0;
    let height = 0;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const ratio = Math.min(window.devicePixelRatio || 1, 2);
      width = Math.max(1, Math.floor(rect.width));
      height = Math.max(1, Math.floor(rect.height));
      canvas.width = Math.floor(width * ratio);
      canvas.height = Math.floor(height * ratio);
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
    };

    const observer = new ResizeObserver(resize);
    observer.observe(canvas);
    resize();

    const render = (time: number) => {
      frame = time * 0.00025;
      context.clearRect(0, 0, width, height);

      const gradient = context.createLinearGradient(0, 0, width, height);
      gradient.addColorStop(0, "rgba(255, 255, 255, 0.82)");
      gradient.addColorStop(0.45, "rgba(248, 237, 229, 0.56)");
      gradient.addColorStop(1, "rgba(220, 231, 241, 0.22)");
      context.fillStyle = gradient;
      context.fillRect(0, 0, width, height);

      const blobs = [
        { x: 0.18, y: 0.2, size: 0.34, color: "rgba(254, 106, 52, 0.20)", speed: 1.0 },
        { x: 0.78, y: 0.3, size: 0.38, color: "rgba(25, 77, 112, 0.16)", speed: -0.7 },
        { x: 0.52, y: 0.72, size: 0.42, color: "rgba(255, 177, 137, 0.15)", speed: 0.55 },
      ];

      for (const blob of blobs) {
        const x = width * (blob.x + Math.sin(frame * blob.speed) * 0.035);
        const y = height * (blob.y + Math.cos(frame * blob.speed * 0.8) * 0.04);
        const radius = Math.min(width, height) * blob.size;
        const radial = context.createRadialGradient(x, y, 0, x, y, radius);
        radial.addColorStop(0, blob.color);
        radial.addColorStop(1, "rgba(255,255,255,0)");
        context.fillStyle = radial;
        context.fillRect(0, 0, width, height);
      }

      animationId = requestAnimationFrame(render);
    };

    animationId = requestAnimationFrame(render);
    return () => {
      observer.disconnect();
      cancelAnimationFrame(animationId);
    };
  }, []);

  return <canvas ref={canvasRef} className="home-shader" aria-hidden="true" />;
}
