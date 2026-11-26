/* AERIX / First iteration. Art direction and adjustable parameters: design-brief.md.
   One GSAP clock drives Lenis, ScrollTrigger and the on-demand Three.js renderer. */
const { gsap, ScrollTrigger, SplitText, Lenis } = window;
const MOTION = { ease: "expo.out", scrollDuration: 1.15, revealDuration: 0.9 };
const mobileQuery = matchMedia("(max-width:760px)"),
  reducedQuery = matchMedia("(prefers-reduced-motion:reduce)");
const body = document.body,
  sections = [...document.querySelectorAll("[data-chapter]")],
  stage = document.querySelector("#visual-stage"),
  stageHome = stage.parentNode,
  stageNext = stage.nextSibling,
  dialog = document.querySelector("#explorer"),
  toggle = document.querySelector("#motion-toggle"),
  loading = document.querySelector("#load-status");
let stored = "";
try {
  stored = localStorage.getItem("aerix-motion") || "";
} catch {}
let wantsMotion = stored !== "off" && !reducedQuery.matches,
  motionOn = wantsMotion && !mobileQuery.matches,
  lenis,
  engine,
  enginePromise,
  story = 0,
  anchors = [],
  opener,
  failed = false,
  lastChapter = -1;
gsap.registerPlugin(ScrollTrigger, SplitText);
gsap.defaults({ ease: MOTION.ease });
function measure() {
  anchors = sections.map((s, i) =>
    i === 0 ? 0 : s.offsetTop + s.offsetHeight / 2 - innerHeight / 2,
  );
  updateStory();
}
function coordinate(y) {
  if (!anchors.length) return 0;
  for (let i = 0; i < anchors.length - 1; i++)
    if (y < anchors[i + 1])
      return i + Math.max(0, (y - anchors[i]) / (anchors[i + 1] - anchors[i]));
  return 7;
}
function updateStory() {
  story = coordinate(window.scrollY);
  const chapter = Math.min(6, Math.round(story));
  if (chapter !== lastChapter) {
    document.querySelectorAll(".chapter-index a").forEach((a, i) => {
      a.classList.toggle("active", i === chapter);
      if (i === chapter) a.setAttribute("aria-current", "step");
      else a.removeAttribute("aria-current");
    });
    lastChapter = chapter;
  }
  if (engine && motionOn && !dialog.open) engine.update(story);
}
function smoothScroll() {
  lenis?.destroy();
  lenis = undefined;
  if (motionOn) {
    lenis = new Lenis({
      duration: MOTION.scrollDuration,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
      syncTouch: false,
      autoRaf: false,
    });
    lenis.on("scroll", ScrollTrigger.update);
  }
}
function motionLabel() {
  toggle.setAttribute("aria-pressed", String(motionOn));
  toggle.setAttribute(
    "aria-label",
    motionOn ? "Turn off animated motion" : "Turn on animated motion",
  );
  toggle.querySelector(".motion-label").textContent = motionOn
    ? "Motion on"
    : "Motion off";
  toggle.querySelector(".motion-icon").textContent = motionOn ? "Ⅱ" : "▷";
}
function fallback() {
  failed = true;
  body.classList.add("is-static");
  body.dataset.renderMode = "static";
  loading.hidden = true;
  engine?.setActive(false);
  if (dialog.open) {
    const status = document.querySelector("#explorer-status");
    status.hidden = false;
    status.textContent =
      "The 3D view could not open. Close this window to continue exploring the design.";
  }
}
async function loadScene() {
  if (engine) return engine;
  if (enginePromise) return enginePromise;
  loading.hidden = false;
  failed = false;
  enginePromise = import("./js/scene.js")
    .then(({ createScene }) =>
      createScene({
        onProgress: (p) => {
          document.querySelector("#load-progress").textContent = p
            ? Math.round(p * 100) + "%"
            : "";
        },
        onFailure: fallback,
      }),
    )
    .then((value) => {
      engine = value;
      loading.hidden = true;
      if (dialog.open) {
        engine.explore("flight");
        engine.resize();
        document.querySelector("#explorer-status").hidden = true;
      } else {
        engine.resize();
        engine.update(story);
        engine.setActive(motionOn);
        engine.render(performance.now());
        if (motionOn) {
          body.classList.remove("is-static");
          body.dataset.renderMode = "live";
        }
      }
      return engine;
    })
    .catch(() => {
      enginePromise = null;
      fallback();
      return null;
    });
  return enginePromise;
}
async function setMotion(on) {
  wantsMotion = on;
  motionOn = on && !mobileQuery.matches;
  motionLabel();
  smoothScroll();
  if (!motionOn) {
    body.classList.add("is-static");
    body.dataset.renderMode = "static";
    engine?.setActive(dialog.open);
  } else {
    const e = await loadScene();
    if (e && !failed && !dialog.open) {
      e.setActive(true);
      e.resize();
      e.update(story);
      body.classList.remove("is-static");
      body.dataset.renderMode = "live";
    }
  }
  measure();
  ScrollTrigger.refresh();
}
toggle.addEventListener("click", () => {
  const on = !motionOn;
  try {
    localStorage.setItem("aerix-motion", on ? "on" : "off");
  } catch {}
  setMotion(on);
});
function navigate(hash) {
  const section = document.querySelector(hash);
  if (!section) return;
  measure();
  const i = sections.indexOf(section),
    y = i >= 0 ? anchors[i] : section.offsetTop;
  if (lenis)
    lenis.scrollTo(y, {
      duration: 1.35,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    });
  else
    window.scrollTo({
      top: y,
      behavior: reducedQuery.matches ? "instant" : "smooth",
    });
  history.replaceState(null, "", hash);
}
document.querySelectorAll('a[href^="#"]').forEach((a) =>
  a.addEventListener("click", (e) => {
    const hash = a.getAttribute("href");
    if (hash.length < 2) return;
    e.preventDefault();
    navigate(hash);
  }),
);
async function openExplorer(e) {
  opener = e.currentTarget;
  dialog.showModal();
  stage.setAttribute("aria-hidden", "false");
  body.classList.add("in-explorer");
  lenis?.stop();
  document.querySelector("#explorer-stage").prepend(stage);
  const status = document.querySelector("#explorer-status");
  status.hidden = !!engine;
  status.textContent = "Opening the view…";
  const value = await loadScene();
  if (!dialog.open) return;
  if (value) {
    value.explore("flight");
    value.resize();
    status.hidden = true;
    document
      .querySelectorAll("[data-pose]")
      .forEach((b) =>
        b.setAttribute("aria-pressed", String(b.dataset.pose === "flight")),
      );
  } else fallback();
}
function closeExplorer() {
  if (!dialog.open) return;
  dialog.close();
  stage.setAttribute("aria-hidden", "true");
  body.classList.remove("in-explorer");
  stageHome.insertBefore(stage, stageNext);
  engine?.close();
  engine?.resize();
  engine?.update(story);
  engine?.setActive(motionOn);
  lenis?.start();
  opener?.focus({ preventScroll: true });
}
document
  .querySelectorAll("[data-explore]")
  .forEach((b) => b.addEventListener("click", openExplorer));
document
  .querySelector("#close-explorer")
  .addEventListener("click", closeExplorer);
dialog.addEventListener("cancel", (e) => {
  e.preventDefault();
  closeExplorer();
});
document.querySelectorAll("[data-pose]").forEach((b) =>
  b.addEventListener("click", () => {
    if (!engine) return;
    engine.explore(b.dataset.pose);
    document
      .querySelectorAll("[data-pose]")
      .forEach((p) => p.setAttribute("aria-pressed", String(p === b)));
  }),
);
// ScrollTrigger observes the same native position that Lenis advances on this ticker.
smoothScroll();
gsap.ticker.lagSmoothing(0);
gsap.ticker.add((time, delta) => {
  lenis?.raf(time * 1000);
  engine?.render(time * 1000);
});
ScrollTrigger.create({
  trigger: "#experience",
  start: "top top",
  end: "bottom bottom",
  onUpdate: updateStory,
  onRefresh: measure,
});
let resizeTimer;
addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    measure();
    engine?.resize();
    ScrollTrigger.refresh();
  }, 120);
});
mobileQuery.addEventListener("change", () => setMotion(wantsMotion));
reducedQuery.addEventListener("change", (e) => setMotion(!e.matches));
addEventListener("visibilitychange", () => {
  if (!document.hidden) {
    measure();
    engine?.resize();
  }
});
await document.fonts.ready;
if (!reducedQuery.matches) {
  const split = SplitText.create(".hero h1", {
    type: "words",
    mask: "words",
    aria: "auto",
  });
  gsap.from(split.words, {
    yPercent: 108,
    autoAlpha: 0,
    duration: 1.25,
    ease: MOTION.ease,
    stagger: 0.065,
  });
  if (motionOn) {
    gsap.from(".hero .eyebrow,.hero .lede,.hero .text-link", {
      autoAlpha: 0,
      y: 16,
      duration: MOTION.revealDuration,
      stagger: 0.1,
      delay: 0.2,
    });
    gsap.utils
      .toArray("[data-reveal]")
      .forEach((el) =>
        gsap.from(el, {
          autoAlpha: 0,
          y: 35,
          duration: MOTION.revealDuration,
          scrollTrigger: {
            trigger: el,
            start: "top 85%",
            toggleActions: "play none none reverse",
          },
        }),
      );
    gsap.to(".hero-watermark", {
      yPercent: -20,
      ease: "none",
      scrollTrigger: {
        trigger: ".hero",
        start: "top top",
        end: "bottom top",
        scrub: true,
      },
    });
  }
}
measure();
motionLabel();
ScrollTrigger.refresh();
if (location.hash && document.querySelector(location.hash))
  setTimeout(() => navigate(location.hash), 100);
body.dataset.renderMode = "static";
if (motionOn) loadScene();
window.aerixInspect = () => ({
  ready: true,
  motionOn,
  mobile: mobileQuery.matches,
  reduced: reducedQuery.matches,
  renderMode: body.dataset.renderMode,
  failed,
  story,
  anchors: [...anchors],
  explorerOpen: dialog.open,
  engine: engine?.inspect(),
});
window.aerixReady = true;
