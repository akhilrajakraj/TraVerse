import "@testing-library/jest-dom";

// jsdom does not implement the Canvas 2D API. The home page uses a canvas
// shader for visual polish, so provide the minimal drawing surface required
// by the component tests without adding the native `canvas` dependency.
HTMLCanvasElement.prototype.getContext = function getContext(kind: string) {
  if (kind !== "2d") return null;

  const gradient = () => ({
    addColorStop: () => undefined,
  });

  return {
    clearRect: () => undefined,
    createLinearGradient: gradient,
    createRadialGradient: gradient,
    fillRect: () => undefined,
    setTransform: () => undefined,
    fillStyle: "",
  } as unknown as CanvasRenderingContext2D;
};
