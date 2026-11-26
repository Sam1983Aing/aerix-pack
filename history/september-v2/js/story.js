// All assembly state is a pure function of scroll. Ambient motion is a separate rig.
import { sampleFlight } from "./flight.js?v=2.2";
export const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
export const smooth = (v, a = 0, b = 1) => {
  const t = clamp((v - a) / (b - a));
  return t * t * (3 - 2 * t);
};
export const lerp = (a, b, t) => a + (b - a) * t;
export const VIEWS = [
  { focus: "whole", dir: [0.27, 0.34, 1], distance: 1.1, x: 0, y: 0.105 },
  { focus: "whole", dir: [0.55, 0.27, 1], distance: 1.14, x: 0.17, y: 0 },
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
  { focus: "whole", dir: [-0.52, 0.2, -1], distance: 1.05, x: 0.21, y: -0.04 },
  { focus: "whole", dir: [-0.35, 0.14, -1], distance: 1.75, x: 0.21, y: -0.13 },
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
const FLIGHT = { ...ALL, battery: 0, thermal: 0, computer: 0, tray: 0 };
const only = (k) =>
  Object.fromEntries(Object.keys(ALL).map((x) => [x, +(x === k)]));
const POSES = [
  CLOSED,
  CLOSED,
  { ...CLOSED, body: 1 },
  { ...CLOSED, body: 1, battery: 1 },
  { ...CLOSED, body: 1, computer: 1, thermal: 1 },
  { ...CLOSED, body: 1, optics: 1 },
  CLOSED,
  CLOSED,
  CLOSED,
];
const WEIGHTS = [
  FLIGHT,
  FLIGHT,
  ALL,
  only("battery"),
  only("computer"),
  only("optics"),
  only("optics"),
  FLIGHT,
  FLIGHT,
];
export function sampleStory(value) {
  const t = clamp(value, 0, 8),
    a = Math.min(7, Math.floor(t)),
    b = a + 1,
    u = t - a,
    v = smooth(u, 0.08, 0.92),
    pose = {},
    weights = {};
  for (const k in CLOSED) pose[k] = lerp(POSES[a][k], POSES[b][k], v);
  for (const k in ALL)
    weights[k] = lerp(WEIGHTS[a][k], WEIGHTS[b][k], smooth(u, 0.15, 0.78));
  if (a === 1) {
    pose.body = smooth(u, 0.18, 0.9);
    for (const k of ["battery", "thermal", "computer", "tray"])
      weights[k] = smooth(pose.body, 0.04, 0.3);
  }
  if (a === 2)
    for (const k in weights)
      if (k !== "battery") weights[k] = 1 - smooth(u, 0.04, 0.4);
  if (a === 3 || a === 4) {
    weights[a === 3 ? "battery" : "computer"] = 1 - smooth(u, 0.06, 0.4);
    weights[a === 3 ? "computer" : "optics"] = smooth(u, 0.28, 0.68);
  }
  if (a === 5) {
    pose.optics = 1 - smooth(u, 0.04, 0.45);
    pose.body = 1 - smooth(u, 0.06, 0.55);
  }
  if (a === 6) Object.assign(weights, FLIGHT);
  const glass = smooth(t, 5.7, 6.02) * (1 - smooth(t, 6.65, 7.05));
  const lensPass = smooth(t, 5.72, 5.87) * (1 - smooth(t, 5.89, 5.99));
  const modelAlpha = 1 - smooth(t, 5.76, 5.94) + smooth(t, 6.55, 6.7);
  const rotors =
    smooth(t, 0.12, 0.65) * (1 - smooth(t, 1.38, 1.86)) + smooth(t, 6.4, 6.58);
  const flight = sampleFlight(t);
  return {
    t,
    a,
    b,
    u,
    pose,
    weights,
    cameraV: a === 5 ? smooth(u, 0.0, 0.92) : v,
    viewXBoost:
      flight.screenX +
      (a === 6 ? 1.3 * smooth(u, 0, 0.25) * (1 - smooth(u, 0.52, 1)) : 0),
    cameraPullback:
      a === 6 ? 1.6 * smooth(u, 0, 0.1) * (1 - smooth(u, 0.35, 1)) : 0,
    lift: 0.3 * smooth(t, 0.08, 1.2),
    bank: flight.roll,
    flight,
    platformAlpha: 1 - smooth(t, 0.78, 1.2),
    rotors,
    glass,
    lensPass,
    modelAlpha,
    sky: 0.88 * smooth(t, 5.76, 6) + 0.12 * smooth(t, 6.65, 7.8),
    haze: smooth(t, 0.4, 2.1),
    labelAlpha: smooth(t, 1.8, 2) * (1 - smooth(t, 2, 2.2)),
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
