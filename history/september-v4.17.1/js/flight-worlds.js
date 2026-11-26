// The city is an optical prologue. Four other environments carry the aircraft.
// All five shots share the scroll clock; no timers or extra RAF.
const clamp = v => Math.max(0, Math.min(1, v));
const ease = (v, a, b) => { const p=clamp((v-a)/(b-a)); return p*p*(3-2*p); };
export const POV_WORLD = {name:'City lights', asset:'flight-city-v4.14.webp'};
export const FLIGHT_WORLDS = [
  {name:'Glacial heights', description:'Follow the light beyond the ridgeline.', asset:'glacial-horizon-v4.webp'},
  {name:'Into the evergreen', description:'A familiar world. An entirely new scale.', asset:'flight-forest-v4.10.webp'},
  {name:'Somewhere beyond', description:'Follow the coastline. Find your own escape.', asset:'flight-resort-v4.14.webp'},
  {name:'Above the everyday', description:'A thousand stories. A different point of view.', asset:'flight-metropolis-v4.17.webp'},
];
export const landscapeEntryAt=t=>ease(t,6.48,6.88);
export const WORLD_TRANSITIONS = [[7.07,7.12],[7.18,7.23],[7.29,7.34]];
export function flightWorldsAt(t) {
  const mixes=WORLD_TRANSITIONS.map(([a,b])=>ease(t,a,b));
  const weights=[1-mixes[0],mixes[0]*(1-mixes[1]),mixes[1]*(1-mixes[2]),mixes[2]];
  const active=weights.indexOf(Math.max(...weights));
  // Captions take turns through the same soft dissolve as their environment.
  return {mixes,weights,active,progress:clamp((t-7)/.43)};
}
