import "@testing-library/jest-dom";

// jsdom does not implement browser-only APIs used by the interactive home page.
// Keep these shims minimal and test-focused; production/browser behavior is unchanged.
if (typeof HTMLCanvasElement !== "undefined") {
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
}

if (typeof ResizeObserver === "undefined") {
  class ResizeObserverMock implements ResizeObserver {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  }

  globalThis.ResizeObserver = ResizeObserverMock;
}
