// AERIX V3 — graphite, copper and restrained studio light. One reversible journey.
// Opaque assemblies, a long orbital departure, a held reveal, then a vertical detail procession.
import { sampleFlight } from "./flight.js?v=3";
export const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
export const smooth = (v, a = 0, b = 1) => {
  const t = clamp((v - a) / (b - a));
  return t * t * (3 - 2 * t);
};
export const lerp = (a, b, t) => a + (b - a) * t;
// Viewport lengths between semantic chapters. Inspection gets time to breathe.
export const CHAPTER_SPANS = [2.5, 5.2, 5.0, 3.3, 3.0, 3.2, 2.6, 1.8];
export function storyOffsets(height) {
  return CHAPTER_SPANS.reduce(
    (out, span) => [...out, out.at(-1) + span * height],
    [0],
  );
}
export function storyToScroll(t, anchors) {
  const a = Math.min(7, Math.floor(clamp(t, 0, 8)));
  return lerp(anchors[a], anchors[a + 1], clamp(t - a));
}
export function scrollToStory(y, anchors) {
  for (let i = 0; i < 8; i++)
    if (y < anchors[i + 1])
      return i + clamp((y - anchors[i]) / (anchors[i + 1] - anchors[i]));
  return 8;
}
export const VIEWS = [
  { focus: "whole", dir: [0.27, 0.34, 1], distance: 1.04, x: 0, y: 0.105 },
  { focus: "whole", dir: [0.55, 0.27, 1], distance: 1.04, x: 0.17, y: 0 },
  {
    focus: "architecture",
    dir: [0.52, 0.36, 1],
    distance: 1.15,
    x: 0.17,
    y: 0,
  },
  { focus: "battery", dir: [0.65, 0.76, 1], distance: 0.47, x: -0.2, y: 0 },
  { focus: "computer", dir: [0.62, 1.15, 1], distance: 0.32, x: 0.2, y: 0 },
  { focus: "optics", dir: [1, 0.35, 0.65], distance: 0.45, x: -0.2, y: 0 },
  { focus: "lens", dir: [0, 0, 1], distance: 0.009, x: 0, y: 0 },
  { focus: "whole", dir: [0.55, 0.24, 1], distance: 1.08, x: 0.2, y: 0.01 },
  { focus: "whole", dir: [0.85, 0.24, 1], distance: 1.38, x: 0.22, y: -0.06 },
];
const CLOSED = {
  body: 0,
  battery: 0,
  optics: 0,
  thermal: 0,
  computer: 0,
  tray: 0,
  fold: 0,
};
const ALL = {
  exterior: 1,
  chassis: 1,
  battery: 1,
  thermal: 1,
  computer: 1,
  tray: 1,
  optics: 1,
};
// Angles remain unwrapped: the camera travels around the object rather than
// interpolating through it when crossing the rear hemisphere.
const key = (t, focus, az, el, distance, x = 0, y = 0) => ({
  t,
  focus,
  az,
  el,
  distance,
  x,
  y,
});
const TAU = Math.PI * 2;
export const CAMERA_KEYS = [
  key(0, "whole", 0.264, 0.317, 1.04, 0, 0.105),
  key(0.38, "whole", 0.34, 0.29, 1.05, 0.08, 0.055),
  key(0.75, "whole", 0.85, 0.2, 1.03, 0.2, 0),
  key(1.02, "whole", 1.6, 0.13, 0.97, 0.23, 0),
  key(1.24, "whole", 2.85, 0.19, 0.98, 0.21, 0.01),
  key(1.43, "whole", 4.1, -0.28, 1.02, 0.18, -0.01),
  key(1.66, "whole", 5.68, 0.14, 1.03, 0.18, 0),
  key(1.84, "architecture", TAU + 0.48, 0.31, 1.16, 0.18, 0),
  key(2.22, "architecture", TAU + 0.57, 0.34, 1.16, 0.18, 0),
  key(2.58, "whole", TAU + 0.86, 0.25, 1.04, 0.19, 0),
  key(2.82, "whole", TAU + 1.28, 0.18, 1.04, 0.17, 0),
  key(3.0, "presentation", TAU + 0.58, 0.51, 0.52, -0.19, -0.025),
  key(3.38, "presentation", TAU + 0.77, 0.56, 0.49, -0.2, 0),
  key(3.72, "presentation", TAU + 0.66, 0.64, 0.48, 0, 0),
  key(3.94, "presentation", TAU + 0.46, 0.8, 0.34, 0.21, 0),
  key(4.3, "presentation", TAU + 0.67, 0.88, 0.34, 0.21, 0),
  key(4.66, "presentation", TAU + 0.68, 0.52, 0.45, 0, 0),
  key(4.94, "presentation", TAU + 0.99, 0.28, 0.45, -0.19, 0),
  key(5.27, "presentation", TAU + 0.9, 0.24, 0.45, -0.19, 0),
  key(5.51, "presentation", TAU + 0.18, 0.07, 0.25, -0.1, 0),
  key(5.7, "opticalPortal", TAU, 0, 0.18, 0, 0),
  key(5.91, "opticalPortal", TAU, 0, 0.006, 0, 0),
  key(6.34, "whole", TAU + 0.48, 0.22, 1.65, 1.45, 0.02),
  key(6.66, "whole", TAU + 0.48, 0.22, 1.4, 1.15, 0.02),
  key(7, "whole", TAU + 0.53, 0.22, 1.08, 0.21, 0.01),
  key(7.42, "whole", TAU + 0.61, 0.21, 1.09, 0.22, 0),
  key(8, "whole", TAU + 0.84, 0.25, 1.38, 0.24, -0.07),
];
export function cameraAt(t) {
  let i = CAMERA_KEYS.findIndex((k) => k.t > t) - 1;
  if (i < 0) i = t >= 8 ? CAMERA_KEYS.length - 2 : 0;
  const a = CAMERA_KEYS[i],
    b = CAMERA_KEYS[i + 1],
    v = smooth(t, a.t, b.t);
  const az = lerp(a.az, b.az, v),
    el = lerp(a.el, b.el, v);
  return {
    a,
    b,
    v,
    dir: [
      Math.sin(az) * Math.cos(el),
      Math.sin(el),
      Math.cos(az) * Math.cos(el),
    ],
  };
}
export const COPY_WINDOWS = [
  [0, 0, 0.52, 0.9],
  [0.58, 0.76, 1.46, 1.7],
  [1.69, 1.86, 2.21, 2.47],
  [2.88, 3.0, 3.4, 3.61],
  [3.72, 3.91, 4.33, 4.54],
  [4.73, 4.94, 5.3, 5.53],
  [5.96, 6.08, 6.44, 6.74],
  [6.71, 6.95, 7.32, 7.6],
  [7.52, 7.78, 8, 9],
];
export function copyAt(t, i) {
  const [start, entered, leave, end] = COPY_WINDOWS[i];
  const enter = start === entered ? 1 : smooth(t, start, entered),
    exit = smooth(t, leave, end);
  return {
    alpha: enter * (1 - exit),
    y: i === 0 ? t * 1.1 : -0.12 * (1 - enter) + 0.21 * exit,
  };
}
export function sampleStory(value) {
  const t = clamp(value, 0, 8),
    flight = sampleFlight(t);
  const pose = {
    ...CLOSED,
    body: smooth(t, 1.7, 1.98) * (1 - smooth(t, 2.25, 2.57)),
  };
  // Detail studies reuse the exact master geometry. Physical travel replaces
  // alpha crossfades; the airframe closes before any study enters the frame.
  const details = {
    battery: {
      visible: t >= 2.84 && t < 3.85,
      progress: smooth(t, 3.04, 3.25) * (1 - smooth(t, 3.43, 3.59)),
      y: 1.05 * (1 - smooth(t, 2.84, 3.01)) - 0.68 * smooth(t, 3.52, 3.82),
    },
    computer: {
      visible: t >= 3.57 && t < 4.8,
      progress: smooth(t, 3.95, 4.16) * (1 - smooth(t, 4.37, 4.54)),
      y: 0.68 * (1 - smooth(t, 3.57, 3.91)) - 0.7 * smooth(t, 4.45, 4.77),
    },
    optics: {
      visible: t >= 4.52 && t < 5.91,
      progress: smooth(t, 4.95, 5.1) * (1 - smooth(t, 5.28, 5.49)),
      y: 0.65 * (1 - smooth(t, 4.52, 4.91)),
    },
  };
  return {
    t,
    a: Math.min(7, Math.floor(t)),
    b: Math.min(8, Math.floor(t) + 1),
    pose,
    weights: ALL,
    details,
    camera: cameraAt(t),
    flight,
    lift: 0.3 * smooth(t, 0.08, 0.86),
    airframeExit: 0.88 * smooth(t, 2.83, 3.16) * (1 - smooth(t, 5.95, 6.3)),
    modelAlpha: t < 3.2 || t >= 6.58 ? 1 : 0,
    platformAlpha: t < 0.97 ? 1 : 0,
    platformDrop: 0.65 * smooth(t, 0.48, 0.97),
    rotors:
      smooth(t, 0.12, 0.65) * (1 - smooth(t, 1.6, 1.8)) +
      smooth(t, 2.49, 2.75) * (1 - smooth(t, 3.12, 3.22)) +
      smooth(t, 6.55, 6.75),
    glass: smooth(t, 5.72, 6.02) * (1 - smooth(t, 6.65, 7.05)),
    lensPass: smooth(t, 5.72, 5.87) * (1 - smooth(t, 5.9, 6.01)),
    sky: 0.88 * smooth(t, 5.8, 6) + 0.12 * smooth(t, 6.65, 7.8),
    labelAlpha: smooth(t, 1.93, 2.02) * (1 - smooth(t, 2.2, 2.35)),
  };
}
export function explorerPose(name) {
  const p = { ...CLOSED },
    weights = {
      exterior: 1,
      chassis: 1,
      battery: 1,
      thermal: 1,
      computer: 1,
      tray: 1,
      optics: 1,
    };
  let view = { ...VIEWS[0], x: 0 };
  if (name === "exploded") {
    p.body = 1;
    view = { ...VIEWS[2], x: 0 };
  }
  if (name === "folded") {
    p.fold = 1;
    view = { ...VIEWS[0], distance: 0.74, dir: [0.45, 0.48, 1], x: 0 };
  }
  if (["battery", "thermal", "computer", "tray", "optics"].includes(name)) {
    p.body = 1;
    p[name] = 1;
    for (const k in weights) weights[k] = +(k === name);
    view =
      name === "thermal"
        ? { focus: "thermal", dir: [0.8, 0.38, 1], distance: 0.34, x: 0 }
        : name === "tray"
          ? { focus: "tray", dir: [0.65, 1.15, 1], distance: 0.32, x: 0 }
          : { ...VIEWS[{ battery: 3, computer: 4, optics: 5 }[name]], x: 0 };
  }
  if (name === "flight" || name === "folded")
    for (const k of ["battery", "thermal", "computer", "tray"]) weights[k] = 0;
  return { pose: p, weights, view };
}
