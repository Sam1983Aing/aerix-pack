// Round 2 (Nov 18), Sam picked Numbered Pins: the leader lines are gone. A numbered glass pin
// sits on each part, matching the number on its label ("01 / BATTERY"), and the current one
// fills in and pulses. Used by anatomy.js (four layers) and performance.js (five board parts).
// The demos of the other two options are frozen in versions/v2-leader-demos.
const NS = "http://www.w3.org/2000/svg";

export function createPin(svg, number) {
  if (!svg.querySelector("#part-pin-glow")) {
    const defs = document.createElementNS(NS, "defs");
    defs.innerHTML = '<radialGradient id="part-pin-glow"><stop offset="0" stop-color="#9fd0f5" stop-opacity=".55"/><stop offset="1" stop-color="#9fd0f5" stop-opacity="0"/></radialGradient>';
    svg.prepend(defs);
  }
  const g = document.createElementNS(NS, "g");
  g.classList.add("part-pin");
  const halo = document.createElementNS(NS, "circle");
  halo.setAttribute("r", "26");
  halo.classList.add("part-pin-halo");
  const pulse = document.createElementNS(NS, "circle");
  pulse.setAttribute("r", "15");
  pulse.classList.add("part-pin-pulse");
  const disc = document.createElementNS(NS, "circle");
  disc.setAttribute("r", "14");
  disc.classList.add("part-pin-disc");
  const text = document.createElementNS(NS, "text");
  text.textContent = number;
  text.setAttribute("text-anchor", "middle");
  text.setAttribute("dominant-baseline", "central");
  text.classList.add("part-pin-text");
  g.append(halo, pulse, disc, text);
  svg.append(g);
  return g;
}

export function placePin(pin, point, alpha, active) {
  pin.setAttribute("transform", `translate(${point.x} ${point.y})`);
  pin.style.opacity = String(alpha);
  pin.classList.toggle("is-current", active);
}
