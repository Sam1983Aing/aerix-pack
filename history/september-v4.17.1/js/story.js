// AERIX V4 — Glacial Titanium. Monumental objects, floating glass, a distant horizon.
// Opaque assemblies, three accumulating glass cards and three settled flight portraits.
import { sampleFlight } from "./flight.js?v=4.14";
export const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
export const smooth = (v, a = 0, b = 1) => {
  const t = clamp((v - a) / (b - a));
  return t * t * (3 - 2 * t);
};
export const lerp = (a, b, t) => a + (b - a) * t;
// Viewport lengths between semantic chapters. Inspection gets time to breathe.
export const CHAPTER_SPANS = [2.5, 7.4, 9.2, 6.6, 11.4, 7.0, 5.0, 10.0];
// Add 3.6 viewport lengths only to the fully open anatomy reading hold.
// Camera, poses and every subsequent transition keep their original semantic keys.
const ANATOMY_BASE_SPAN = 5.6, ANATOMY_EXTRA = 3.6, ANATOMY_HOLD_END = .22;
const anatomyScroll = p => (p*ANATOMY_BASE_SPAN+ANATOMY_EXTRA*clamp(p/ANATOMY_HOLD_END))/CHAPTER_SPANS[2];
const anatomyStory = p => {
  const distance=p*CHAPTER_SPANS[2],boundary=ANATOMY_HOLD_END*ANATOMY_BASE_SPAN+ANATOMY_EXTRA;
  return distance<=boundary?distance/(ANATOMY_BASE_SPAN+ANATOMY_EXTRA/ANATOMY_HOLD_END):(distance-ANATOMY_EXTRA)/ANATOMY_BASE_SPAN;
};
// Reading time belongs to the closed cartridge and fully open cell stack.
// The opening motion and departure keep their accepted semantic camera keys.
const POWER_BASE_SPAN=4, POWER_CLOSED_EXTRA=.8, POWER_OPEN_EXTRA=1.8;
const powerDistance=p=>p*POWER_BASE_SPAN
  + POWER_CLOSED_EXTRA*clamp(p/.04)
  + POWER_OPEN_EXTRA*clamp((p-.26)/.14);
const powerScroll=p=>powerDistance(p)/CHAPTER_SPANS[3];
const powerStory=p=>{
  const distance=p*CHAPTER_SPANS[3],stops=[0,.04,.26,.4,1];
  for(let i=1;i<stops.length;i++){
    const lo=stops[i-1],hi=stops[i],from=powerDistance(lo),to=powerDistance(hi);
    if(distance<=to)return lerp(lo,hi,(distance-from)/(to-from));
  }
  return 1;
};
// V4.9 gives the second motherboard card 1.8 extra viewport lengths during
// the open study. Its arrival and the following lens transition keep their pace.
const CONTROL_BASE_SPAN = 4, CONTROL_EXTRA = 1.8, CONTROL_HOLD = [.16, .33];
// V4.12: the five surface callouts get a dedicated hold while the board is open.
const PERFORMANCE_EXTRA = 5.6, PERFORMANCE_HOLD = [.33, .37];
const controlDistance = p => p*CONTROL_BASE_SPAN
  + CONTROL_EXTRA*clamp((p-CONTROL_HOLD[0])/(CONTROL_HOLD[1]-CONTROL_HOLD[0]))
  + PERFORMANCE_EXTRA*clamp((p-PERFORMANCE_HOLD[0])/(PERFORMANCE_HOLD[1]-PERFORMANCE_HOLD[0]));
const controlScroll = p => controlDistance(p)/CHAPTER_SPANS[4];
const controlStory = p => {
  const distance=p*CHAPTER_SPANS[4], stops=[0,.16,.33,.37,1];
  for(let i=1;i<stops.length;i++) {
    const lo=stops[i-1],hi=stops[i],from=controlDistance(lo),to=controlDistance(hi);
    if(distance<=to)return lerp(lo,hi,(distance-from)/(to-from));
  }
  return 1;
};
export const performanceFraming = t => smooth(t,4.330,4.338)*(1-smooth(t,4.365,4.370));
// The two optical cards share the fully open study; the lens entrance keeps
// its accepted pace. Additional reading distance belongs only to this hold.
const OPTICS_BASE_SPAN=4, OPTICS_EXTRA=1.6, OPTICS_HOLD=[.10,.28], LENS_HOLD_EXTRA=1.4;
const opticsDistance=p=>p*OPTICS_BASE_SPAN
  +OPTICS_EXTRA*clamp((p-OPTICS_HOLD[0])/(OPTICS_HOLD[1]-OPTICS_HOLD[0]))
  +LENS_HOLD_EXTRA*clamp((p-.86)/.14);
const opticsScroll=p=>opticsDistance(p)/CHAPTER_SPANS[5];
const opticsStory=p=>{
  const distance=p*CHAPTER_SPANS[5],stops=[0,.10,.28,.86,1];
  for(let i=1;i<stops.length;i++){
    const lo=stops[i-1],hi=stops[i],from=opticsDistance(lo),to=opticsDistance(hi);
    if(distance<=to)return lerp(lo,hi,(distance-from)/(to-from));
  }
  return 1;
};
export const opticsFraming=t=>smooth(t,4.95,5.10)*(1-smooth(t,5.28,5.49));
// Spend six extra viewports in the four landscapes, preserving the pace of
// the incoming lens reveal and the departure into the final product portrait.
const SKY_BASE_SPAN=2.6, SKY_EXTRA=6, SKY_HOLD_END=.43, LANDING_EXTRA=1.4;
const skyDistance=p=>p*SKY_BASE_SPAN+SKY_EXTRA*clamp(p/SKY_HOLD_END)+LANDING_EXTRA*clamp((p-.56)/.44);
const skyScroll=p=>skyDistance(p)/CHAPTER_SPANS[7];
const skyStory=p=>{
  const distance=p*CHAPTER_SPANS[7],stops=[0,.43,.56,1];
  for(let i=1;i<stops.length;i++){const lo=stops[i-1],hi=stops[i];if(distance<=skyDistance(hi))return lerp(lo,hi,(distance-skyDistance(lo))/(skyDistance(hi)-skyDistance(lo)));}
  return 1;
};
export const visorAt=t=>smooth(t,5.72,6.02)*(1-smooth(t,7.43,7.78));
// Keep the flat reticle, but introduce the rounded glass only after the real rim
// and its city message have cleared. This also gates the shader's lens distortion.
export const povLensAt=t=>smooth(t,6.46,6.84)*(1-smooth(t,7.43,7.78));
// Hold the real lens rim around the first city image while its message is read.
// The opening then passes beyond the viewport before the aircraft returns.
export function lensPortalAt(t) {
  const arrive=smooth(t,5.76,5.86),release=smooth(t,6.14,6.36);
  return {
    alpha:smooth(t,5.70,5.78)*(1-smooth(t,6.36,6.44)),
    // Match the camera's forward push, so the image does not cover the metal
    // rim ahead of the text exit. Perspective expands inversely with distance.
    radius:(3.1+42.5*Math.pow(arrive,2.5))*.038/(.038-.032*release*release),
    release,
  };
}
export function storyOffsets(height) {
  return CHAPTER_SPANS.reduce(
    (out, span) => [...out, out.at(-1) + span * height],
    [0],
  );
}
export function storyToScroll(t, anchors) {
  const a = Math.min(7, Math.floor(clamp(t, 0, 8)));
  const fraction=clamp(t-a);
  return lerp(anchors[a], anchors[a + 1], a===2?anatomyScroll(fraction):a===3?powerScroll(fraction):a===4?controlScroll(fraction):a===5?opticsScroll(fraction):a===7?skyScroll(fraction):fraction);
}
export function scrollToStory(y, anchors) {
  for (let i = 0; i < 8; i++)
    if (y < anchors[i + 1]) {
      const fraction=clamp((y - anchors[i]) / (anchors[i + 1] - anchors[i]));
      return i + (i===2?anatomyStory(fraction):i===3?powerStory(fraction):i===4?controlStory(fraction):i===5?opticsStory(fraction):i===7?skyStory(fraction):fraction);
    }
  return 8;
}
export const VIEWS = [
  {
    focus: "whole",
    dir: [0.24803, 0.31172, 0.91723],
    distance: 1.0,
    x: 0,
    y: 0.045,
  },
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
// Camera moves are authored in angles so transitions stay outside the object.
// Each card arrival carries one restrained camera move, followed by a reading hold.
const key = (t, focus, az, el, distance, x = 0, y = 0) => ({
  t,
  focus,
  az,
  el,
  distance,
  x,
  y,
});
export const CAMERA_KEYS = [
  key(0, "whole", 0.264, 0.317, 1.0, 0, 0.045),
  key(0.38, "whole", 0.34, 0.29, 1.02, 0.04, 0.035),
  key(0.72, "lens", 0.42, 0.14, 0.54, 0.08, -0.04),
  key(0.94, "whole", 0.35, 0.22, 0.82, 0.17, -0.07),
  key(1.10, "whole", 0.35, 0.22, 0.82, 0.17, -0.07),
  key(1.28, "whole", -0.1, 0.2, 0.94, 0, -0.18),
  key(1.39, "whole", -0.1, 0.2, 0.94, 0, -0.18),
  key(1.57, "whole", -0.55, 0.22, 0.80, -0.10, -0.185),
  key(1.67, "whole", -0.55, 0.22, 0.80, -0.10, -0.185),
  key(1.98, "architecture", 0.48, 0.3, 1.19, 0.02, -0.03),
  key(2.23, "architecture", 0.57, 0.34, 1.19, 0.02, -0.03),
  key(2.58, "whole", 0.88, 0.2, 0.88, 0.04, -0.04),
  key(2.82, "whole", 1.25, 0.16, 0.9, 0.03, -0.04),
  key(3.02, "presentation", 0.62, 0.38, 0.48, -0.1, -0.07),
  key(3.33, "presentation", 0.82, 0.45, 0.49, -0.13, -0.06),
  key(3.52, "presentation", 0.78, 0.55, 0.4, -0.1, -0.08),
  key(3.72, "presentation", 0.55, 0.65, 0.48, 0.02, -0.06),
  key(3.94, "presentation", 0.38, 0.62, 0.3, 0.12, -0.06),
  key(4.2, "presentation", 0.65, 0.74, 0.3, 0.1, -0.06),
  key(4.43, "presentation", 0.82, 0.38, 0.28, 0.1, -0.06),
  key(4.66, "presentation", 0.7, 0.44, 0.43, 0.02, -0.05),
  key(4.94, "presentation", 0.99, 0.25, 0.35, 0.04, -0.1),
  key(5.2, "presentation", 0.87, 0.22, 0.35, 0.04, -0.1),
  key(5.51, "presentation", 0.18, 0.07, 0.24, 0, -0.02),
  key(5.7, "opticalPortal", 0, 0, 0.18, 0, 0),
  key(5.86, "opticalPortal", 0, 0, 0.038, 0, 0),
  key(6.14, "opticalPortal", 0, 0, 0.038, 0, 0),
  key(6.36, "opticalPortal", 0, 0, 0.006, 0, 0),
  key(6.44, "opticalPortal", 0, 0, 0.006, 0, 0),
  // Reposition only while both 3D rigs are hidden. The incoming aircraft is
  // already outside the viewport when made visible, then glides into the shot.
  key(6.64, "whole", 0.48, 0.22, 1.3, 1.4, -0.06),
  key(6.74, "whole", 0.48, 0.22, 1.3, 1.4, -0.06),
  key(7, "whole", 0.46, 0.18, 0.94, 0, -0.085),
  key(7.15, "whole", 0.94, 0.21, 0.86, 0.055, -0.12),
  key(7.26, "whole", 1.35, 0.16, 0.78, -0.06, -0.10),
  key(7.40, "whole", 0.15, 0.20, 0.90, 0.02, -0.085),
  key(7.68, "approach", 0.35, 0.30, 1.04, 0.15, 0.035),
  key(7.94, "landing", 0.35, 0.32, 1.04, 0.15, 0.035),
  key(8, "landing", 0.35, 0.32, 1.04, 0.15, 0.035),
];

export function cameraAt(t) {
  let i = CAMERA_KEYS.findIndex((k) => k.t > t) - 1;
  if (i < 0) i = t >= 8 ? CAMERA_KEYS.length - 2 : 0;
  const start = CAMERA_KEYS[i], end = CAMERA_KEYS[i + 1];
  const progress = smooth(t, start.t, end.t);
  // Let the rim remain recognizable during the first half of the message fade.
  const v = start.t === 6.14 ? progress * progress : progress;
  // A shallow rising arc accompanies the third portrait's dolly-in. Both ends
  // have zero velocity, so the reading holds remain perfectly still.
  const bow = start.t === 1.39 ? Math.sin(Math.PI*v)**2 : 0;
  const arc = k => bow ? {...k,x:k.x+.018*bow,y:k.y-.035*bow} : k;
  const frame=performanceFraming(t);
  const optical=opticsFraming(t);
  const compose = k => {
    const out=frame ? {...k,distance:lerp(k.distance,.33,frame),x:lerp(k.x,0,frame),y:lerp(k.y,.015,frame)} : k;
    return optical?{...out,x:lerp(out.x,0,optical),y:out.y-.045*optical}:out;
  };
  const a=compose(arc(start)), b=compose(arc(end));
  const az = lerp(lerp(a.az, b.az, v),.65,frame),
    el = lerp(lerp(a.el, b.el, v),.74,frame);
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
  [0.76, 0.94, 1.67, 1.77],
  [1.78, 1.98, 2.22, 2.46],
  [2.88, 3.0, 3.4, 3.61],
  [3.72, 3.91, 4.33, 4.54],
  [4.73, 4.94, 5.3, 5.53],
  [5.83, 5.96, 6.14, 6.36],
  [6.89, 7.0, 7.43, 7.56],
  [7.56, 7.8, 8, 9],
];
export function copyAt(t, i) {
  const [start, entered, leave, end] = COPY_WINDOWS[i];
  const enter = start === entered ? 1 : smooth(t, start, entered),
    exit = smooth(t, leave, end);
  return {
    alpha: enter * (1 - exit),
    y: i === 0 ? t * 1.1 : i === 1 ? 0 : -0.12 * (1 - enter) + 0.21 * exit,
  };
}
// One glass card yields to the next; the first is clear before the detail arrives.
// This state uses the page's existing clock and reverses exactly with scrolling.
export function powerCardsAt(t) {
  const leave=smooth(t,3.13,3.19),enter=smooth(t,3.20,3.26);
  return [
    {alpha:1-leave,y:-14*leave,visible:t>=2.88&&t<3.19},
    {alpha:enter,y:18*(1-enter),visible:t>=3.20&&t<3.61},
  ];
}
export function controlCardsAt(t) {
  const leave=smooth(t,4.10,4.17),enter=smooth(t,4.18,4.23);
  const detailsLeave=smooth(t,4.330,4.336);
  return [
    {alpha:1-leave,y:-14*leave,visible:t>=3.72&&t<4.17,active:t<4.18},
    {alpha:enter*(1-detailsLeave),y:18*(1-enter)-14*detailsLeave,visible:t>=4.18&&t<4.336,active:t>=4.18&&t<4.336},
  ];
}
// Desktop cards form one balanced pair. A phone reads them in the same slot,
// clearing the overview before the light-path diagram arrives.
export function opticsCardsAt(t,compact=false) {
  const enter=smooth(t,compact?5.115:5.08,compact?5.15:5.14);
  const leave=compact?smooth(t,5.07,5.105):0;
  return [
    {alpha:1-leave,y:-10*leave,visible:t>=4.73&&t<5.53&&(!compact||t<5.105)},
    {alpha:enter,y:12*(1-enter),visible:t>=(compact?5.115:5.08)&&t<5.53},
  ];
}
// Each card enters its own permanent slot. Settled cards never move as later
// cards arrive; the whole row leaves with its chapter. Pure sampling reverses cleanly.
export const FLIGHT_CARD_WINDOWS = [
  [0.78, 0.94],
  [1.10, 1.28],
  [1.39, 1.57],
];
export function flightCardsAt(t) {
  // Pass the spotlight after the incoming card has started becoming legible.
  const second=smooth(t,1.14,1.28),third=smooth(t,1.43,1.57);
  const focus=[1-second,second*(1-third),third];
  const active=focus.indexOf(Math.max(...focus));
  return FLIGHT_CARD_WINDOWS.map(([start, entered], i) => {
    const reveal = smooth(t, start, entered);
    return {
      x: 22 * (1 - reveal),
      alpha: reveal*(.66+.34*focus[i]),
      focus: focus[i],
      visible: t >= start && t < 1.77,
      settled: t >= entered,
      active: i === active,
    };
  });
}
export function sampleStory(value) {
  const t = clamp(value, 0, 8),
    flight = sampleFlight(t);
  const pose = {
    ...CLOSED,
    body: smooth(t, 1.77, 1.98) * (1 - smooth(t, 2.25, 2.57)),
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
      visible: t >= 4.52 && t < 6.36,
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
    lift: 0.3 * smooth(t, 0.08, 0.86)*(1-smooth(t,7.72,7.97)),
    airframeExit: 0.88 * smooth(t, 2.83, 3.16) * (1 - smooth(t, 5.95, 6.3)),
    modelAlpha: t < 3.2 || t >= 6.72 ? 1 : 0,
    platformAlpha: t < 0.97 || t>=7.44 ? 1 : 0,
    platformDrop: t>=7.43 ? .9*(1-smooth(t,7.43,7.74)) : 0.65 * smooth(t, 0.48, 0.97),
    rotors:
      smooth(t, 0.12, 0.65) * (1 - smooth(t, 1.72, 1.9)) +
      smooth(t, 2.49, 2.75) * (1 - smooth(t, 3.12, 3.22)) +
      smooth(t, 6.55, 6.75)*(1-smooth(t,7.88,7.995)),
    glass: povLensAt(t),
    lensPass: lensPortalAt(t).alpha,
    sky: smooth(t, 5.8, 5.86) * (1 - smooth(t, 7.43, 7.83)),
    // The city initially exists only inside the clipped lens opening. Prepare
    // the full-screen backdrop after that opening covers every viewport corner,
    // before the portal overlay starts fading at 6.36.
    backgroundSky: smooth(t, 6.28, 6.36) * (1 - smooth(t, 7.43, 7.83)),
    labelAlpha: 0,
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
