// The city is an optical prologue. Four other environments carry the aircraft.
// All five shots share the scroll clock; no timers or extra RAF.
// `local` is the still for each world (assets/worlds/), streamed per chapter. Round 2: `clip` is
// its Seedance 2.5 video (720p, no audio). The still is the clip's first frame.
const clamp = v => Math.max(0, Math.min(1, v));
const ease = (v, a, b) => { const p=clamp((v-a)/(b-a)); return p*p*(3-2*p); };
export const POV_WORLD = {name:'City lights', asset:'flight-city-v4.14.webp', local:'worlds/city.webp', clip:'worlds/clips/city.mp4'};
export const FLIGHT_WORLDS = [
  {name:'Glacial heights', description:'Follow the light beyond the ridgeline.', asset:'glacial-horizon-v4.webp', local:'worlds/glacial.webp', clip:'worlds/clips/glacial.mp4'},
  {name:'Into the evergreen', description:'A familiar world. An entirely new scale.', asset:'flight-forest-v4.10.webp', local:'worlds/forest.webp', clip:'worlds/clips/forest.mp4'},
  {name:'Somewhere beyond', description:'Follow the coastline. Find your own escape.', asset:'flight-resort-v4.14.webp', local:'worlds/resort.webp', clip:'worlds/clips/resort.mp4'},
  {name:'Above the everyday', description:'A thousand stories. A different point of view.', asset:'flight-metropolis-v4.17.webp', local:'worlds/metropolis.webp', clip:'worlds/clips/metropolis.mp4'},
];
export const landscapeEntryAt=t=>ease(t,6.48,6.88);
// Sam, Nov 19: each clip runs as one continuous shot. It starts from frame 0 (its still) the moment
// its world starts to appear: the city as the lens opens, each landscape as its blend begins.
// The scroll then waits at the end of that world, just before the next blend, until the clip
// has played in full (see the clip hold in main.js). After CLIP_ENDS the world is out of sight.
export const CLIP_STARTS = [5.70, 6.48, 7.07, 7.18, 7.29];
export const CLIP_HOLDS = [6.47, 7.064, 7.174, 7.284, 7.42];
export const CLIP_ENDS = [6.88, 7.12, 7.23, 7.34, 7.78];
export const WORLD_TRANSITIONS = [[7.07,7.12],[7.18,7.23],[7.29,7.34]];
export function flightWorldsAt(t) {
  const mixes=WORLD_TRANSITIONS.map(([a,b])=>ease(t,a,b));
  const weights=[1-mixes[0],mixes[0]*(1-mixes[1]),mixes[1]*(1-mixes[2]),mixes[2]];
  const active=weights.indexOf(Math.max(...weights));
  // Captions take turns through the same soft dissolve as their environment.
  return {mixes,weights,active,progress:clamp((t-7)/.43)};
}
