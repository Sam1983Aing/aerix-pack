// A three-face type drum. Its centre and line box never move, so the last face
// becomes the existing scroll-driven hero title without a scale or layout jump.
export function createHeroTitle({ gsap, heading, onComplete }) {
  const faces = [...heading.querySelectorAll(".hero-title-face")];
  const state = { turn: 180 };
  let timeline;
  function paint() {
    heading.style.setProperty("--title-turn", `${state.turn}deg`);
    faces.forEach((face, i) => {
      const angle = state.turn - i * 90;
      const facing = Math.cos((angle * Math.PI) / 180);
      face.style.visibility = facing > 0.001 ? "visible" : "hidden";
      face.style.setProperty(
        "--face-light",
        String(0.4 + Math.max(0, facing) * 0.6),
      );
    });
  }
  const resize = () => {
    heading.style.setProperty("--title-depth", `${heading.clientHeight / 2}px`);
  };
  new ResizeObserver(resize).observe(heading);
  function prepare() {
    timeline?.kill();
    timeline = null;
    state.turn = 0;
    resize();
    paint();
  }
  function finish() {
    timeline?.kill();
    timeline = null;
    state.turn = 180;
    paint();
  }
  function play({ paused = false } = {}) {
    prepare();
    timeline = gsap.timeline({ paused, onComplete });
    timeline
      .to(
        state,
        { turn: 90, duration: 0.8, ease: "power3.inOut", onUpdate: paint },
        0.7,
      )
      .to(
        state,
        { turn: 180, duration: 0.95, ease: "power3.inOut", onUpdate: paint },
        2.05,
      )
      .to({}, { duration: 0.18 });
  }
  return {
    prepare,
    finish,
    play,
    preview(seconds) {
      if (!timeline) play({ paused: true });
      timeline.pause().seek(Math.max(0, Math.min(3.18, seconds)), true);
      paint();
    },
    inspect: () => ({
      turn: state.turn,
      time: timeline?.time() ?? 3.18,
      playing: timeline?.isActive() ?? false,
      visible: faces
        .filter((f) => f.style.visibility !== "hidden")
        .map((f) => f.textContent.trim()),
    }),
  };
}
