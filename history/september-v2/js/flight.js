// AERIX flight direction: bank into a curved departure, settle for inspection,
// then counter-bank through the open sky. Angles are radians; distances are metres.
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const smooth = (v, a, b) => {
  const x = clamp((v - a) / (b - a));
  return x * x * (3 - 2 * x);
};
export const FLIGHT_TUNING = Object.freeze({
  takeoffYaw: -0.3,
  takeoffBank: -0.12,
  hoverHeight: 0.006,
  hoverWidth: 0.0035,
  responseBank: 0.035,
  responseSeconds: 0.22,
});

// The main path is purely scroll-driven, so every bank reverses with the page.
export function sampleFlight(t) {
  const departure = smooth(t, 0.22, 0.78) * (1 - smooth(t, 1.02, 1.78));
  const correction = smooth(t, 0.78, 1.16) * (1 - smooth(t, 1.3, 1.82));
  const sky = smooth(t, 6.55, 6.95);
  const departureEnd = smooth(t, 7.18, 8);
  return {
    yaw:
      FLIGHT_TUNING.takeoffYaw * departure +
      0.055 * correction +
      sky * (0.2 - 0.36 * departureEnd),
    roll:
      FLIGHT_TUNING.takeoffBank * departure +
      0.042 * correction +
      sky * (-0.105 + 0.16 * departureEnd),
    pitch:
      0.055 * departure -
      0.025 * correction +
      sky * (0.04 - 0.1 * departureEnd),
    x: 0.018 * departure - 0.008 * correction,
    z: -0.012 * departure,
    screenX: -0.045 * departure - 0.025 * sky * (1 - departureEnd),
    airborne: smooth(t, 0.22, 0.64) * (1 - smooth(t, 1.4, 1.84)) + sky,
  };
}

// Slow stabilization survives a pause in scrolling. It disappears before macro
// inspection and is disabled entirely by the reduced-motion/static paths.
export function sampleHover(seconds, weight, pointer, drive) {
  return {
    x:
      weight *
      (Math.sin(seconds * 0.77) * FLIGHT_TUNING.hoverWidth + pointer.x * 0.002),
    y:
      weight *
      (Math.sin(seconds * 1.17) * FLIGHT_TUNING.hoverHeight +
        Math.sin(seconds * 0.43) * 0.0015),
    z: weight * Math.sin(seconds * 0.61) * 0.002,
    yaw: weight * (Math.sin(seconds * 0.58) * 0.026 + pointer.x * 0.025),
    roll:
      weight *
      (Math.sin(seconds * 0.83) * 0.018 +
        pointer.x * 0.022 -
        drive * FLIGHT_TUNING.responseBank),
    pitch:
      weight *
      (Math.sin(seconds * 0.69) * 0.012 + pointer.y * 0.012 + drive * 0.017),
  };
}
