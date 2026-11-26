/* Pure scroll state: every pose is recomputed from position, so reversing, jumping
   chapters and resizing cannot leave an assembly partially open. */
export const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
export const smooth = (v, a = 0, b = 1) => {
  const t = clamp((v - a) / (b - a));
  return t * t * (3 - 2 * t);
};
export const lerp = (a, b, t) => a + (b - a) * t;
export const VIEWS = [
  { focus: "whole", dir: [0.48, 0.53, 0.9], distance: 1.1, x: 0.18 },
  { focus: "whole", dir: [0.8, 0.36, -0.64], distance: 0.94, x: 0.2 },
  { focus: "whole", dir: [0.55, 0.45, 1], distance: 1.1, x: 0.21 },
  { focus: "battery", dir: [0.65, 0.76, 1], distance: 0.47, x: -0.21 },
  { focus: "computer", dir: [0.62, 1.15, 1], distance: 0.3, x: 0.22 },
  { focus: "optics", dir: [1, 0.35, 0.65], distance: 0.47, x: -0.2 },
  { focus: "whole", dir: [0.5, 0.55, 1], distance: 0.7, x: 0.21 },
  { focus: "whole", dir: [0.5, 0.43, 1], distance: 1.07, x: 0.18 },
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
const POSES = [
  CLOSED,
  CLOSED,
  { ...CLOSED, body: 1 },
  { ...CLOSED, body: 1, battery: 1 },
  { ...CLOSED, body: 1, thermal: 1, computer: 1 },
  { ...CLOSED, body: 1, optics: 1 },
  { ...CLOSED, fold: 1 },
  CLOSED,
];
const WEIGHTS = [
  {
    exterior: 1,
    chassis: 1,
    battery: 0,
    thermal: 0,
    computer: 0,
    tray: 0,
    optics: 1,
  },
  {
    exterior: 1,
    chassis: 1,
    battery: 0,
    thermal: 0,
    computer: 0,
    tray: 0,
    optics: 1,
  },
  {
    exterior: 1,
    chassis: 1,
    battery: 1,
    thermal: 1,
    computer: 1,
    tray: 1,
    optics: 1,
  },
  {
    exterior: 0,
    chassis: 0,
    battery: 1,
    thermal: 0,
    computer: 0,
    tray: 0,
    optics: 0,
  },
  {
    exterior: 0,
    chassis: 0,
    battery: 0,
    thermal: 0,
    computer: 1,
    tray: 0,
    optics: 0,
  },
  {
    exterior: 0,
    chassis: 0,
    battery: 0,
    thermal: 0,
    computer: 0,
    tray: 0,
    optics: 1,
  },
  {
    exterior: 1,
    chassis: 1,
    battery: 0,
    thermal: 0,
    computer: 0,
    tray: 0,
    optics: 1,
  },
  {
    exterior: 1,
    chassis: 1,
    battery: 0,
    thermal: 0,
    computer: 0,
    tray: 0,
    optics: 1,
  },
];
export function sampleStory(value) {
  const t = clamp(value, 0, 7),
    a = Math.min(6, Math.floor(t)),
    b = a + 1,
    u = t - a,
    v = smooth(u, 0.08, 0.9),
    pose = {},
    weights = {};
  for (const key in CLOSED) pose[key] = lerp(POSES[a][key], POSES[b][key], v);
  for (const key in WEIGHTS[0])
    weights[key] = lerp(WEIGHTS[a][key], WEIGHTS[b][key], smooth(u, 0.22, 0.8));
  // The optics close, then the body reassembles, then the blades and arms fold.
  if (a === 5) {
    pose.optics = 1 - smooth(u, 0, 0.22);
    pose.body = 1 - smooth(u, 0.22, 0.65);
    pose.fold = smooth(u, 0.72, 1);
    weights.battery =
      weights.thermal =
      weights.computer =
      weights.tray =
        smooth(u, 0.18, 0.32) * (1 - smooth(u, 0.52, 0.65));
  }
  if (a === 1) {
    pose.body = smooth(u, 0.18, 0.9);
    for (const key of ["battery", "thermal", "computer", "tray"])
      weights[key] = smooth(pose.body, 0.06, 0.32);
  }
  // Clear the surrounding silhouette before approaching a single assembly.
  if (a === 2) {
    for (const key of [
      "exterior",
      "chassis",
      "thermal",
      "computer",
      "tray",
      "optics",
    ])
      weights[key] = 1 - smooth(u, 0.06, 0.4);
  }
  let cameraV = v,
    cameraPullback = 0;
  if (a === 3 || a === 4) {
    cameraV = smooth(u, 0.02, 0.68);
    const outgoing = a === 3 ? "battery" : "computer";
    const incoming = a === 3 ? "computer" : "optics";
    weights[outgoing] = 1 - smooth(u, 0.08, 0.4);
    weights[incoming] = smooth(u, 0.26, 0.65);
  }
  if (a === 5) {
    cameraV = smooth(u, 0.02, 0.7);
    cameraPullback = 0.42 * smooth(u, 0.1, 0.45) * (1 - smooth(u, 0.9, 1));
    weights.exterior = weights.chassis = smooth(u, 0.12, 0.36);
  }
  return {
    t,
    a,
    b,
    u,
    v,
    cameraV,
    cameraPullback,
    pose,
    weights,
    labelAlpha:
      a === 1 ? smooth(u, 0.75, 1) : a === 2 ? 1 - smooth(u, 0, 0.25) : 0,
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
    view = { ...VIEWS[6], x: 0 };
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
