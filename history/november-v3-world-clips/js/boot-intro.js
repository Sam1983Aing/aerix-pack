// The model is uploaded and its first frame completed before the count begins.
// A bounded presentation clock keeps a slow/returning frame from skipping 100.
export const BOOT_DURATION = 5.4;
export function createBootIntro({ gsap, root, onRevealChange, onComplete }) {
  const faces = [...root.querySelectorAll('.boot-status-face')];
  const message = root.querySelector('#boot-message');
  const counter = root.querySelector('#boot-percent');
  const status = root.querySelector('#boot-status');
  const state = { progress: 0, turn: 0, light: 0, ink: 1, ui: 0 };
  // ThreeUI polish: the count can run ahead while the model streams, up to where loading is.
  let timeline, ready = false, reviewing = false, current = -1, elapsed = 0, loadingProgress = 0;
  function paint() {
    root.style.setProperty('--boot-ink', state.ink);
    message.style.setProperty('--boot-turn', `${state.turn}deg`);
    counter.textContent = String(Math.floor(state.progress + .00001)).padStart(2, '0');
    faces.forEach((face, i) => {
      const facing = Math.cos((state.turn - i * 90) * Math.PI / 180);
      face.style.visibility = facing > .001 ? 'visible' : 'hidden';
      face.style.setProperty('--face-light', String(.3 + Math.max(0, facing) * .7));
    });
    const index = Math.round(state.turn / 90);
    if (index !== current) {
      current = index;
      status.textContent = faces[index].textContent;
    }
    onRevealChange({ light: state.light, ui: state.ui, prepared: ready || reviewing });
  }
  function start({ paused = false } = {}) {
    timeline?.kill();
    ready = false; reviewing = paused; current = -1; elapsed = 0; loadingProgress = 0;
    Object.assign(state, { progress: 0, turn: 0, light: 0, ink: 1, ui: 0 });
    root.hidden = false;
    root.setAttribute('aria-busy', 'true');
    paint();
    timeline = gsap.timeline({ paused: true, onUpdate: paint, onComplete });
    timeline
      .to(state, { progress: 34, duration: 1.1, ease: 'none' }, 0)
      .to(state, { turn: 90, duration: .64, ease: 'power3.inOut' }, .86)
      .to(state, { progress: 68, duration: 1.1, ease: 'none' }, 1.1)
      .to(state, { turn: 180, duration: .64, ease: 'power3.inOut' }, 1.96)
      .to(state, { progress: 100, duration: 1, ease: 'none' }, 2.2)
      // The counter holds at 100 while the same hero scene starts to illuminate.
      .to(state, { light: 1, duration: 2.05, ease: 'power1.inOut' }, 3.35)
      .to(state, { ink: 0, duration: .45, ease: 'power2.inOut' }, 3.85)
      .to(state, { ui: 1, duration: 1.05, ease: 'power2.inOut' }, 4.35);
  }
  return {
    start,
    loadProgress(value) { loadingProgress = Math.max(loadingProgress, Math.min(.99, Math.max(0, value))); },
    ready() { ready = true; paint(); },
    tick(deltaMs) {
      if (!timeline || reviewing || elapsed >= BOOT_DURATION) return;
      // Before the hero frame is ready, the timeline may only advance to the loaded share.
      const limit = ready ? BOOT_DURATION : loadingProgress * 3.2;
      elapsed = Math.min(limit, elapsed + Math.max(0, Math.min(50, deltaMs)) / 1000);
      timeline.time(elapsed, false);
    },
    finish() {
      timeline?.kill(); timeline = null;
      root.hidden = true;
      root.setAttribute('aria-busy', 'false');
    },
    preview(seconds) {
      if (!timeline) start({ paused: true });
      reviewing = true;
      elapsed = Math.max(0, Math.min(BOOT_DURATION, seconds));
      timeline.pause().seek(elapsed, true);
      paint();
    },
    inspect: () => ({
      time: elapsed,
      progress: +counter.textContent,
      turn: state.turn,
      light: state.light,
      opacity: state.ink,
      ui: state.ui,
      message: status.textContent,
      visible: faces.filter(f => f.style.visibility !== 'hidden').map(f => f.textContent.trim()),
      waiting: !ready && !reviewing, ready, reviewing,
      playing: !!timeline && (ready || loadingProgress > 0) && !reviewing && elapsed < (ready ? BOOT_DURATION : loadingProgress * 3.2),
    }),
  };
}
