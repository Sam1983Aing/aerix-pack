/* AERIX V2. One clock, reversible scroll state, independent assembly and flight rigs. */
import { clamp, smooth } from "./js/story.js?v=2.2";
const { gsap, ScrollTrigger, Lenis } = window;
gsap.registerPlugin(ScrollTrigger);
gsap.ticker.lagSmoothing(0);
const body = document.body,
  sections = [...document.querySelectorAll("[data-chapter]")],
  experience = document.querySelector("#experience"),
  stage = document.querySelector("#visual-stage"),
  stageHome = stage.parentNode,
  stageNext = stage.nextSibling,
  dialog = document.querySelector("#explorer"),
  toggle = document.querySelector("#motion-toggle"),
  loading = document.querySelector("#load-status"),
  boot = document.querySelector("#awakening");
const mobileQuery = matchMedia("(max-width:760px)"),
  reducedQuery = matchMedia("(prefers-reduced-motion:reduce)");
let stored = "",
  seen = false;
try {
  stored = localStorage.getItem("aerix-motion") || "";
  seen = sessionStorage.getItem("aerix-v2-intro") === "seen";
} catch {}
let wantsMotion = stored !== "off" && !reducedQuery.matches,
  motionOn = wantsMotion && !mobileQuery.matches,
  engine,
  enginePromise,
  lenis,
  story = 0,
  step = innerHeight * 1.28,
  anchors = [],
  failed = false,
  opener,
  booting = false,
  bootSkipped = false,
  introTween,
  live = false,
  lastChapter = -1,
  lastDOM = -99;
const phases = [
  "PRE-FLIGHT",
  "DEPARTURE",
  "SUSPENSION",
  "ENERGY",
  "INTELLIGENCE",
  "OPTICAL AXIS",
  "FIRST PERSON",
  "OPEN SKY",
  "FURTHER",
];
function introEnd() {
  introTween?.kill();
  introTween = null;
  booting = false;
  boot.hidden = true;
  body.classList.remove("is-booting");
  body.style.overflow = "";
  document.querySelector(".site-header").inert = false;
  experience.inert = false;
  document.querySelector(".bottom-tools").inert = false;
  engine?.setIntro(1);
  lenis?.start();
  try {
    sessionStorage.setItem("aerix-v2-intro", "seen");
  } catch {}
  updateStory(true);
}
function introStart() {
  booting = true;
  boot.hidden = false;
  body.classList.add("is-booting");
  body.style.overflow = "hidden";
  document.querySelector(".site-header").inert = true;
  experience.inert = true;
  document.querySelector(".bottom-tools").inert = true;
  boot.style.setProperty("--boot-brand", ".45");
  document.querySelector("#skip-intro").focus({ preventScroll: true });
}
function introPlay() {
  if (!booting || bootSkipped) {
    engine?.setIntro(1);
    return;
  }
  boot.classList.add("ready");
  lenis?.stop();
  engine.setIntro(0);
  document.querySelector("#boot-message").textContent = "OPTICS ONLINE";
  document.querySelector("#boot-percent").textContent = "READY";
  const state = { v: 0 };
  introTween = gsap.to(state, {
    v: 1,
    duration: 3.6,
    ease: "none",
    onUpdate() {
      const v = state.v;
      engine.setIntro(v);
      boot.style.setProperty(
        "--boot-brand",
        smooth(v, 0.2, 0.45) * (1 - smooth(v, 0.75, 1)),
      );
      boot.style.setProperty(
        "--scan-alpha",
        smooth(v, 0.06, 0.2) * (1 - smooth(v, 0.58, 0.7)),
      );
      boot.style.setProperty(
        "--scan-x",
        -innerWidth * 0.05 + innerWidth * 1.15 * smooth(v, 0.08, 0.68) + "px",
      );
      boot.style.setProperty(
        "--halo-alpha",
        smooth(v, 0.1, 0.18) * (1 - smooth(v, 0.28, 0.46)),
      );
    },
    onComplete: introEnd,
  });
}
document.querySelector("#skip-intro").addEventListener("click", () => {
  bootSkipped = true;
  introEnd();
  document.querySelector(".wordmark").focus({ preventScroll: true });
});
function motionLabel() {
  toggle.hidden = mobileQuery.matches;
  toggle.setAttribute("aria-pressed", String(motionOn && !failed));
  toggle.setAttribute(
    "aria-label",
    motionOn && !failed
      ? "Turn off animated motion"
      : "Turn on animated motion",
  );
  toggle.querySelector(".motion-label").textContent =
    motionOn && !failed ? "Motion on" : "Motion off";
  toggle.querySelector(".motion-icon").textContent =
    motionOn && !failed ? "Ⅱ" : "▷";
}
function measure() {
  step = innerHeight * 1.28;
  if (live) {
    experience.style.height = innerHeight + 8 * step + "px";
    anchors = sections.map((_, i) => i * step);
  } else {
    experience.style.height = "";
    anchors = sections.map((s) => s.offsetTop);
  }
  updateStory(true);
}
function coordinate(y) {
  if (live) return clamp(y / step, 0, 8);
  for (let i = 0; i < anchors.length - 1; i++)
    if (y < anchors[i + 1])
      return i + clamp((y - anchors[i]) / (anchors[i + 1] - anchors[i]));
  return 8;
}
function updateStory(force = false) {
  story = coordinate(scrollY);
  if (!force && Math.abs(story - lastDOM) < 0.000001) return;
  lastDOM = story;
  const chapter = Math.round(story);
  if (chapter !== lastChapter) {
    document.querySelector("#altitude").textContent = String(chapter).padStart(
      2,
      "0",
    );
    document.querySelector("#phase-name").textContent = phases[chapter];
    const activeNav =
      chapter < 2 ? "#ascent" : chapter < 6 ? "#architecture" : "#perspective";
    document.querySelectorAll(".site-header nav a").forEach((a) => {
      if (a.getAttribute("href") === activeNav)
        a.setAttribute("aria-current", "step");
      else a.removeAttribute("aria-current");
    });
    lastChapter = chapter;
  }
  document.querySelector("#phase-number").textContent = story
    .toFixed(2)
    .padStart(5, "0");
  document.querySelector(".altimeter-track i").style.bottom =
    (story / 8) * 100 + "%";
  if (live) {
    sections.forEach((section, i) => {
      const delta = story - i;
      const alpha =
        (1 - smooth(Math.abs(delta), 0.16, 0.56)) *
        (i === 0 ? 1 - smooth(story, 0.1, 0.38) : 1) *
        (i === 6
          ? smooth(story, 5.89, 6)
          : i === 5
            ? 1 - smooth(story, 5.2, 5.52)
            : 1);
      section.style.transform = `translate3d(0,${delta * innerHeight * 0.83}px,0)`;
      section.style.opacity = alpha;
      section.inert = alpha < 0.06;
      section.setAttribute("aria-hidden", String(alpha < 0.006));
    });
    const glass = smooth(story, 5.7, 6.02) * (1 - smooth(story, 6.65, 7.05));
    document.querySelector(".optical-glass").style.opacity = glass;
    document.querySelector(".lens-transition").style.opacity =
      smooth(story, 5.72, 5.87) * (1 - smooth(story, 5.89, 5.99));
    body.classList.toggle("is-light", story > 5.97);
  }
  if (engine && motionOn && !dialog.open && !booting) engine.update(story);
}
function smoothScroll() {
  lenis?.destroy();
  lenis = undefined;
  if (live) {
    lenis = new Lenis({
      duration: 1.23,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
      syncTouch: false,
      autoRaf: false,
    });
    lenis.on("scroll", () => {
      ScrollTrigger.update();
      updateStory();
    });
    if (booting) lenis.stop();
  }
}
function setLive(on) {
  const before = story;
  live = on;
  body.classList.toggle("is-live", on);
  body.classList.toggle("is-static", !on);
  body.dataset.renderMode = on ? "live" : "static";
  if (!on) {
    body.classList.remove("is-light");
    sections.forEach((s) => {
      s.style.transform = "";
      s.style.opacity = "";
      s.removeAttribute("aria-hidden");
      s.inert = false;
    });
    document.querySelector(".optical-glass").style.opacity = 0;
    document.querySelector(".lens-transition").style.opacity = 0;
  }
  measure();
  smoothScroll();
  window.scrollTo({
    top: on ? before * step : anchors[Math.round(before)],
    behavior: "instant",
  });
  measure();
  ScrollTrigger.refresh();
  engine?.resize();
  updateStory(true);
}
function fallback() {
  failed = true;
  motionOn = false;
  introEnd();
  setLive(false);
  loading.hidden = true;
  engine?.dispose();
  engine = undefined;
  enginePromise = null;
  motionLabel();
  if (dialog.open) {
    const status = document.querySelector("#explorer-status");
    status.hidden = false;
    status.textContent =
      "The 3D view could not open. Close this window to explore the design in images.";
  }
}
async function loadScene() {
  if (engine) return engine;
  if (enginePromise) return enginePromise;
  failed = false;
  loading.hidden = false;
  enginePromise = import("./js/scene.js?v=2.2")
    .then(({ createScene }) =>
      createScene({
        onProgress: (p) => {
          const percent = Math.round(p * 100);
          document.querySelector("#load-progress").textContent = p
            ? percent + "%"
            : "";
          document.querySelector("#boot-percent").textContent = p
            ? String(percent).padStart(2, "0")
            : "CONNECTING";
          boot.style.setProperty("--load-progress", percent + "%");
          if (p === 1)
            document.querySelector("#boot-message").textContent =
              "CALIBRATING LIGHT";
        },
        onFailure: fallback,
      }),
    )
    .then((value) => {
      engine = value;
      loading.hidden = true;
      engine.setCinematic(!reducedQuery.matches);
      if (dialog.open) {
        engine.explore("flight");
        engine.resize();
        document.querySelector("#explorer-status").hidden = true;
      } else if (motionOn) {
        setLive(true);
        engine.setActive(true);
        engine.update(story);
        engine.render(performance.now());
        introPlay();
      } else {
        engine.setActive(false);
        introEnd();
      }
      return value;
    })
    .catch((error) => {
      console.error("AERIX scene:", error);
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
  if (!motionOn) {
    introEnd();
    setLive(false);
    engine?.setActive(dialog.open);
  } else {
    const value = await loadScene();
    if (value && !failed && !dialog.open) {
      setLive(true);
      value.setActive(true);
      value.setIntro(1);
    }
  }
}
toggle.addEventListener("click", () => {
  const on = !motionOn;
  try {
    localStorage.setItem("aerix-motion", on ? "on" : "off");
  } catch {}
  setMotion(on);
});
function navigate(hash, instant = false) {
  const index = sections.findIndex((s) => "#" + s.id === hash);
  if (index < 0) return;
  if (booting) {
    bootSkipped = true;
    introEnd();
  }
  measure();
  const y = anchors[index];
  if (lenis && !instant) lenis.scrollTo(y, { duration: 1.65 });
  else
    window.scrollTo({
      top: y,
      behavior: instant || reducedQuery.matches ? "instant" : "smooth",
    });
  history.replaceState(null, "", hash);
}
document.querySelectorAll('a[href^="#"]').forEach((a) =>
  a.addEventListener("click", (e) => {
    const hash = a.getAttribute("href");
    if (hash.length > 1) {
      e.preventDefault();
      navigate(hash);
    }
  }),
);
async function openExplorer(e) {
  opener = e.currentTarget;
  if (booting) introEnd();
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
      .forEach((q) => q.setAttribute("aria-pressed", String(q === b)));
  }),
);
let pointer = { x: 0, y: 0 };
addEventListener("pointermove", (e) => {
  pointer.x = (e.clientX / innerWidth - 0.5) * 2;
  pointer.y = (e.clientY / innerHeight - 0.5) * 2;
});
gsap.ticker.add((t) => {
  lenis?.raf(t * 1000);
  engine?.setPointer(pointer.x, pointer.y);
  engine?.render(t * 1000);
  if (live && !reducedQuery.matches) {
    body.style.setProperty("--pointer-x", pointer.x * 1.2 + "deg");
    body.style.setProperty("--pointer-y", -pointer.y * 0.6 + "deg");
  }
});
ScrollTrigger.create({
  trigger: experience,
  start: "top top",
  end: "bottom bottom",
  onUpdate: () => updateStory(),
});
addEventListener("scroll", () => updateStory(), { passive: true });
let resizeTimer;
addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    const previous = story;
    measure();
    lenis?.resize();
    if (live) {
      if (lenis) lenis.scrollTo(previous * step, { immediate: true });
      else window.scrollTo(0, previous * step);
    }
    engine?.resize();
    ScrollTrigger.refresh();
  }, 140);
});
mobileQuery.addEventListener("change", () => setMotion(wantsMotion));
reducedQuery.addEventListener("change", (e) => {
  engine?.setCinematic(!e.matches);
  setMotion(!e.matches);
});
addEventListener("visibilitychange", () => {
  if (!document.hidden) {
    measure();
    engine?.resize();
  }
});
measure();
motionLabel();
if (motionOn) {
  if (!seen && !location.hash && scrollY < 30) introStart();
  loadScene().then(() => {
    if (location.hash) navigate(location.hash, true);
  });
} else if (location.hash)
  requestAnimationFrame(() => navigate(location.hash, true));
window.aerixInspect = () => ({
  ready: true,
  version: 2,
  motionOn,
  mobile: mobileQuery.matches,
  reduced: reducedQuery.matches,
  renderMode: body.dataset.renderMode,
  failed,
  story,
  anchors: [...anchors],
  explorerOpen: dialog.open,
  booting,
  engine: engine?.inspect(),
});
window.aerixReady = true;

if (new URLSearchParams(location.search).has("qa"))
  window.aerixQA = {
    seek: (t) => {
      if (lenis) lenis.scrollTo(clamp(t, 0, 8) * step, { immediate: true });
      else window.scrollTo(0, clamp(t, 0, 8) * step);
      updateStory(true);
    },
    capture: (name) => engine?.capture(name),
    inspectSurface: (options) => engine?.captureInspection(options),
    anchors: () => engine?.verifyFramingContract(),
  };
