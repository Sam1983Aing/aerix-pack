// Round 2 demo (Nov 18): three ways to connect a part to its label, in the anatomy chapter
// and on the flight computer. Picked with ?leaders=<slug>. Without it, nothing changes.
//   straight  Straight Shot: labels keep their tidy rows, each leader is one clean stroke.
//   level     Level Lines: each label slides to its part's height, every leader is horizontal.
//   pins      Numbered Pins: no leaders. A numbered pin sits on each part and lights up with its label.
export const LEADERS = (() => {
  const v = new URLSearchParams(location.search).get("leaders");
  return ["straight", "level", "pins"].includes(v) ? v : null;
})();

const NS = "http://www.w3.org/2000/svg";

// Level Lines: choose label tops so each anchor sits inside its own label's band, labels never
// overlap, and the anchor lands as close as possible to the label's icon row (top + offset).
// items: [{ anchor, height }] in any order. Returns the tops in the same order.
export function solveLevel(items, { gap = 10, offset = 28, min = 70, max = Infinity } = {}) {
  const order = items.map((item, i) => ({ ...item, i })).sort((a, b) => a.anchor - b.anchor);
  const lo = (it) => it.anchor - it.height + 6, hi = (it) => it.anchor - 6;
  for (const it of order) it.top = Math.min(hi(it), Math.max(lo(it), it.anchor - offset));
  for (let pass = 0; pass < 24; pass++) {
    for (let k = 1; k < order.length; k++) {
      const prev = order[k - 1], it = order[k];
      it.top = Math.max(it.top, prev.top + prev.height + gap);
    }
    for (let k = order.length - 2; k >= 0; k--) {
      const next = order[k + 1], it = order[k];
      it.top = Math.min(it.top, next.top - it.height - gap);
    }
    for (const it of order) it.top = Math.min(hi(it), Math.max(lo(it), it.top));
  }
  // Labels never overlap, even when two anchors are too close to both stay inside their bands.
  for (let k = 1; k < order.length; k++) order[k].top = Math.max(order[k].top, order[k - 1].top + order[k - 1].height + gap);
  for (const it of order) it.top = Math.max(min, Math.min(max - it.height, it.top));
  const tops = [];
  for (const it of order) tops[it.i] = it.top;
  return tops;
}

// Numbered Pins: a small glass disc with the part's number, and a ring that pulses while current.
// Level Lines on the board: the processor and IMU sit only ~30px apart on screen, so their
// leaders start on the processor's upper edge and the IMU's lower edge instead of their centres.
export const LEVEL_NUDGE = { processor: -22, imu: 14 };

export function createPin(svg, number) {
  if (!svg.querySelector("#leader-pin-glow")) {
    const defs = document.createElementNS(NS, "defs");
    defs.innerHTML = '<radialGradient id="leader-pin-glow"><stop offset="0" stop-color="#9fd0f5" stop-opacity=".55"/><stop offset="1" stop-color="#9fd0f5" stop-opacity="0"/></radialGradient>';
    svg.prepend(defs);
  }
  const g = document.createElementNS(NS, "g");
  g.classList.add("leader-pin");
  const halo = document.createElementNS(NS, "circle");
  halo.setAttribute("r", "26");
  halo.classList.add("leader-pin-halo");
  const pulse = document.createElementNS(NS, "circle");
  pulse.setAttribute("r", "15");
  pulse.classList.add("leader-pin-pulse");
  const disc = document.createElementNS(NS, "circle");
  disc.setAttribute("r", "14");
  disc.classList.add("leader-pin-disc");
  const text = document.createElementNS(NS, "text");
  text.textContent = number;
  text.setAttribute("text-anchor", "middle");
  text.setAttribute("dominant-baseline", "central");
  text.classList.add("leader-pin-text");
  g.append(halo, pulse, disc, text);
  svg.append(g);
  return g;
}
export function placePin(pin, point, alpha, active) {
  pin.setAttribute("transform", `translate(${point.x} ${point.y})`);
  pin.style.opacity = String(alpha);
  pin.classList.toggle("is-current", active);
}

// Shared look for the demo, injected once.
if (LEADERS) {
  const style = document.createElement("style");
  style.textContent = `
    .leader-pin-halo { fill: url(#leader-pin-glow); opacity: .55; }
    .leader-pin-disc { fill: rgb(8 22 40 / .86); stroke: #b8e0ff; stroke-width: 1.5; }
    .leader-pin-text { fill: #f2f9ff; font: 400 11px var(--mono); letter-spacing: .02em; }
    .leader-pin.is-current .leader-pin-halo { opacity: 1; }
    .leader-pin-pulse { fill: none; stroke: #9fd0f5; stroke-width: 1; opacity: 0; transform-box: fill-box; transform-origin: center; }
    .leader-pin.is-current .leader-pin-disc { fill: #9fd0f5; }
    .leader-pin.is-current .leader-pin-text { fill: #08162a; }
    .leader-pin.is-current .leader-pin-pulse { animation: leader-pin-pulse 1.6s ease-out infinite; }
    @keyframes leader-pin-pulse { 0% { opacity: .9; transform: scale(1); } 100% { opacity: 0; transform: scale(2.1); } }
    body[data-leaders="level"] .anatomy-label:not(.is-current) .anatomy-note,
    body[data-leaders="level"] .performance-label:not(.is-current) .performance-note { display: none; }
    body[data-leaders="pins"] .anatomy-leaders path,
    body[data-leaders="pins"] .performance-leaders path,
    body[data-leaders="pins"] .anatomy-leaders g:not(.leader-pin) > circle,
    body[data-leaders="pins"] .performance-leaders g:not(.leader-pin) > circle { display: none; }
  `;
  document.head.append(style);
  document.body.dataset.leaders = LEADERS;
}
