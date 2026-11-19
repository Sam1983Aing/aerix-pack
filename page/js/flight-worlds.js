// Free pack version: the September stills, no clips. The video version plays Seedance clips
// made on Higgsfield, which stay with the video. Put your own 16:9 MP4 in `clip` to bring them back.
// The city is an optical prologue. Four other environments carry the aircraft.
// All five shots share the scroll clock; no timers or extra RAF.
// `local` is the still for each world (assets/worlds/), streamed per chapter. `clip` is its
// Seedance 2.5 video (no audio), upscaled to 4K with Topaz, round 3 from Nov 19: Banff lake, Canadian autumn path,
// lagoon resort at sunset, Times Square at night. The still is the clip's first frame.
const clamp = v => Math.max(0, Math.min(1, v));
const ease = (v, a, b) => { const p=clamp((v-a)/(b-a)); return p*p*(3-2*p); };
// Sam, Nov 19: the city is the original lit harbour still again (worlds/city.webp, the same
// picture the lens opening uses in styles.css), with no clip. Its video started
// with a visible skip as the lens opened, so the motion begins with the landscapes instead.
export const POV_WORLD = {name:'City lights', asset:'flight-city-v4.14.webp', local:'worlds/city.webp', clip:null};
export const FLIGHT_WORLDS = [
  {name:'Glacial heights', description:'Follow the light beyond the ridgeline.', asset:'glacial-horizon-v4.webp', local:'worlds/glacial.webp', clip:null},
  {name:'Into the evergreen', description:'A familiar world. An entirely new scale.', asset:'flight-forest-v4.10.webp', local:'worlds/forest.webp', clip:null},
  {name:'Somewhere beyond', description:'Follow the coastline. Find your own escape.', asset:'flight-resort-v4.14.webp', local:'worlds/resort.webp', clip:null},
  {name:'Above the everyday', description:'A thousand stories. A different point of view.', asset:'flight-metropolis-v4.17.webp', local:'worlds/metropolis.webp', clip:null},
];
export const landscapeEntryAt=t=>ease(t,6.48,6.88);
// Sam, Nov 19: each clip runs as one continuous shot. It starts from frame 0 (its still) the moment
// its world starts to appear, as its blend begins.
// The scroll then waits at the end of that world, just before the next blend, until the clip
// has played in full (see the clip hold in main.js). After CLIP_ENDS the world is out of sight.
// Index 0 (the city) has no clip, so no start and no hold.
export const CLIP_STARTS = [null, 6.48, 7.07, 7.18, 7.29];
export const CLIP_HOLDS = [null, 7.064, 7.174, 7.284, 7.42];
export const CLIP_ENDS = [6.88, 7.12, 7.23, 7.34, 7.78];
export const WORLD_TRANSITIONS = [[7.07,7.12],[7.18,7.23],[7.29,7.34]];
export function flightWorldsAt(t) {
  const mixes=WORLD_TRANSITIONS.map(([a,b])=>ease(t,a,b));
  const weights=[1-mixes[0],mixes[0]*(1-mixes[1]),mixes[1]*(1-mixes[2]),mixes[2]];
  const active=weights.indexOf(Math.max(...weights));
  // Captions take turns through the same soft dissolve as their environment.
  return {mixes,weights,active,progress:clamp((t-7)/.43)};
}
