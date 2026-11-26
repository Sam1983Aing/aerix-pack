/* AERIX V4 — Glacial Titanium. One clock, reversible scroll state, independent assembly and flight rigs. */
import { createBootIntro, BOOT_DURATION } from "./js/boot-intro.js?v=4.7";
import { createHeroTitle } from "./js/hero-title.js?v=4.2";
import {flightWorldsAt} from './js/flight-worlds.js?v=4.17';
import {createPreorder} from './js/preorder.js?v=4.16.1';
import {
  clamp,
  smooth,
  copyAt,
  flightCardsAt,
  powerCardsAt,
  controlCardsAt,
  opticsCardsAt,
  visorAt,
  povLensAt,
  lensPortalAt,
  storyOffsets,
  storyToScroll,
  scrollToStory,
} from "./js/story.js?v=4.17.1";
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
  flightCards = [...document.querySelectorAll("[data-flight-card]")],
  flightSteps = [...document.querySelectorAll(".flight-steps i")],
  flightNumber = document.querySelector("[data-flight-number]"),
  powerCards = [...document.querySelectorAll("[data-power-card]")],
  controlCards = [...document.querySelectorAll("[data-control-card]")],
  opticsCards = [...document.querySelectorAll("[data-optics-card]")],
  worldCaptions = [...document.querySelectorAll('[data-world]')],
  worldStops = [...document.querySelectorAll('.world-stops li')],
  loading = document.querySelector("#load-status"),
  boot = document.querySelector("#awakening");
const mobileQuery = matchMedia("(max-width:760px)"),
  reducedQuery = matchMedia("(prefers-reduced-motion:reduce)");
// Cinematic is the sole presentation. OS accessibility and WebGL failure retain
// readable content; the former motion toggle and its saved preference are retired.
let motionOn = !reducedQuery.matches,
  engine,
  enginePromise,
  lenis,
  story = 0,
  anchors = [],
  failed = false,
  opener,
  booting = false,
  introRequest = 0,
  heroRevealing = false,
  live = false,
  lastChapter = -1,
  lastDOM = -99;
const preorder=createPreorder({
  onFinish:id=>engine?.setFinish(id),
  onOpen:()=>{lenis?.stop();body.classList.add('in-preorder');},
  onClose:()=>{body.classList.remove('in-preorder');lenis?.start();},
});
// Replay on refresh, including from a chapter. Fresh chapter links still open directly.
const replayIntroOnLoad =
  motionOn &&
  (!location.hash ||
    performance.getEntriesByType("navigation")[0]?.type === "reload");
if (replayIntroOnLoad) {
  history.scrollRestoration = "manual";
  if (location.hash)
    history.replaceState(null, "", location.pathname + location.search);
  window.scrollTo({ top: 0, left: 0, behavior: "instant" });
}
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
const heroTitle = createHeroTitle({
  gsap,
  heading: document.querySelector(".hero-title"),
  onComplete: heroRevealEnd,
});
const bootIntro = createBootIntro({
  gsap,
  root: boot,
  onRevealChange: ({ light, ui, prepared }) => {
    body.classList.toggle("is-boot-prepared", prepared);
    body.style.setProperty("--boot-ui", ui);
    engine?.setIntro(light);
  },
  onComplete: () => introEnd({ revealHero: true }),
});
const titleSkip = document.querySelector(".hero-title-skip");
function heroRevealEnd() {
  const wasRevealing = heroRevealing;
  heroTitle.finish();
  heroRevealing = false;
  titleSkip.hidden = true;
  body.classList.remove("is-title-revealing");
  if (!booting) {
    body.style.overflow = "";
    if (wasRevealing) {
      if (lenis) lenis.scrollTo(0, { immediate: true, force: true });
      else window.scrollTo({ top: 0, behavior: "instant" });
    }
    lenis?.start();
  }
  updateStory(true);
}
function heroRevealStart({ paused = false } = {}) {
  if (booting || !motionOn || !live || failed) return false;
  heroRevealing = true;
  titleSkip.hidden = false;
  body.classList.add("is-title-revealing");
  body.style.overflow = "hidden";
  lenis?.stop();
  if (lenis) lenis.scrollTo(0, { immediate: true, force: true });
  else window.scrollTo({ top: 0, behavior: "instant" });
  engine?.setIntro(1);
  updateStory(true);
  heroTitle.play({ paused });
  return true;
}
titleSkip.addEventListener("click", () => {
  heroRevealEnd();
  document.querySelector(".hero .scroll-cue").focus({ preventScroll: true });
});
function introEnd({ revealHero = false } = {}) {
  introRequest++;
  bootIntro.finish();
  if (booting) {
    if (lenis) lenis.scrollTo(0, { immediate: true, force: true });
    else window.scrollTo({ top: 0, left: 0, behavior: "instant" });
  }
  booting = false;
  boot.hidden = true;
  body.classList.remove("is-booting", "is-boot-prepared");
  body.style.removeProperty("--boot-ui");
  body.style.overflow = "";
  document.querySelector(".site-header").inert = false;
  experience.inert = false;
  document.querySelector(".bottom-tools").inert = false;
  engine?.setIntro(1);
  if (revealHero && motionOn && !failed) heroRevealStart();
  else heroRevealEnd();
  if (document.activeElement === boot)
    document.querySelector(".wordmark").focus({ preventScroll: true });
}
function introStart({ paused = false } = {}) {
  introRequest++;
  heroRevealEnd();
  heroTitle.prepare();
  booting = true;
  boot.hidden = false;
  body.classList.add("is-booting");
  body.style.overflow = "hidden";
  document.querySelector(".site-header").inert = true;
  experience.inert = true;
  document.querySelector(".bottom-tools").inert = true;
  bootIntro.start({ paused });
  if (lenis) lenis.scrollTo(0, { immediate: true, force: true });
  else window.scrollTo({ top: 0, left: 0, behavior: "instant" });
  updateStory(true);
  engine?.update(0);
  engine?.setIntro(0);
  document.querySelector(".hero h1").style.opacity = "1";
  boot.focus({ preventScroll: true });
}
async function introPlay() {
  if (!booting) return;
  const request = introRequest;
  lenis?.stop();
  try {
    // Compile, upload and complete the first actual GPU frame before counting.
    await Promise.all([engine.warmIntro(), document.fonts.ready]);
    if (booting && request === introRequest) bootIntro.ready();
  } catch (error) {
    console.error("AERIX illumination:", error);
    fallback();
  }
}
function measure() {
  if (live) {
    anchors = storyOffsets(innerHeight);
    experience.style.height = innerHeight + anchors[8] + "px";
  } else {
    experience.style.height = "";
    anchors = sections.map((s) => s.offsetTop);
  }
  updateStory(true);
}
function coordinate(y) {
  if (live) return scrollToStory(y, anchors);
  for (let i = 0; i < anchors.length - 1; i++)
    if (y < anchors[i + 1])
      return i + clamp((y - anchors[i]) / (anchors[i + 1] - anchors[i]));
  return 8;
}
function updateStory(force = false) {
  story = booting || heroRevealing ? 0 : coordinate(scrollY);
  if (!force && Math.abs(story - lastDOM) < 0.000001) return;
  lastDOM = story;
  let chapter = Math.floor(story),
    strongest = 0.1;
  sections.forEach((_, i) => {
    const a = copyAt(story, i).alpha;
    if (a > strongest) {
      chapter = i;
      strongest = a;
    }
  });
  if (story >= 2.43 && story < 2.95) chapter = 2;
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
    const worlds=flightWorldsAt(story);
    worldCaptions.forEach((caption,i)=>{
      caption.style.opacity=worlds.weights[i];
      caption.style.transform=`translateY(${7*(1-worlds.weights[i])}px)`;
      caption.setAttribute('aria-hidden',String(i!==worlds.active));
      worldStops[i].classList.toggle('is-current',i===worlds.active);
      if(i===worlds.active) worldStops[i].setAttribute('aria-current','step');
      else worldStops[i].removeAttribute('aria-current');
    });
    powerCardsAt(story).forEach((state,i)=>{
      const card=powerCards[i];
      card.style.setProperty('--power-y',`${state.y}px`);
      card.style.opacity=state.alpha;
      card.style.visibility=state.visible?'visible':'hidden';
      card.inert=!state.visible||state.alpha<.06;
      card.setAttribute('aria-hidden',String(!state.visible||state.alpha<.006));
    });
    controlCardsAt(story).forEach((state,i)=>{
      const card=controlCards[i];
      card.style.setProperty('--control-y',`${state.y}px`);
      card.style.opacity=state.alpha;
      card.style.visibility=state.visible?'visible':'hidden';
      card.inert=!state.visible||state.alpha<.06;
      card.setAttribute('aria-hidden',String(!state.visible||state.alpha<.006));
    });
    opticsCardsAt(story,mobileQuery.matches).forEach((state,i)=>{
      const card=opticsCards[i];
      card.style.setProperty('--optics-y',`${state.y}px`);
      card.style.opacity=state.alpha;
      card.style.visibility=state.visible?'visible':'hidden';
      card.inert=!state.visible||state.alpha<.06;
      card.setAttribute('aria-hidden',String(!state.visible||state.alpha<.006));
    });
    const cards = flightCardsAt(story);
    flightCards.forEach((card, i) => {
      const state = cards[i];
      card.style.setProperty("--flight-x", `${state.x}%`);
      card.style.setProperty('--flight-focus',state.focus);
      card.classList.toggle('is-active',state.active);
      if(state.active)card.setAttribute('aria-current','step');
      else card.removeAttribute('aria-current');
      card.style.opacity = state.alpha;
      card.style.visibility = state.visible ? "visible" : "hidden";
      card.inert = !state.visible;
      card.setAttribute("aria-hidden", String(!state.visible));
      flightSteps[i].classList.toggle("is-current", state.active);
      flightSteps[i].classList.toggle("is-complete", state.settled);
      if (state.active)
        flightNumber.textContent = String(i + 1).padStart(2, "0");
    });
    sections.forEach((section, i) => {
      const { alpha, y } = copyAt(story, i);
      section.style.transform = `translate3d(0,${y * innerHeight}px,0)`;
      section.style.opacity = alpha;
      section.inert = alpha < 0.06;
      section.setAttribute("aria-hidden", String(alpha < 0.006));
    });
    const bridge = document.querySelector(".flight-bridge");
    const bridgeIn = smooth(story, 2.43, 2.6),
      bridgeOut = smooth(story, 2.79, 2.97);
    bridge.style.opacity = bridgeIn * (1 - bridgeOut);
    bridge.style.transform = `translateY(${(-0.1 * (1 - bridgeIn) + 0.16 * bridgeOut) * innerHeight}px)`;
    bridge.setAttribute(
      "aria-hidden",
      String(bridgeIn * (1 - bridgeOut) < 0.006),
    );
    bridge.inert = bridgeIn * (1 - bridgeOut) < 0.06;
    const glass = visorAt(story);
    document.querySelector(".optical-glass").style.opacity = glass;
    document.querySelector('.optical-glass').style.setProperty('--visor-edge-opacity',.9*povLensAt(story));
    document.querySelector('.optical-glass').style.setProperty('--visor-hud-opacity',.68-.4*copyAt(story,6).alpha);
    const portal=lensPortalAt(story);
    document.querySelector(".lens-transition").style.opacity = portal.alpha;
    document
      .querySelector(".lens-transition")
      .style.setProperty(
        "--portal-radius",
        portal.radius + "vmax",
      );
    body.classList.toggle("is-light", story > 5.97 && story < 7.6);
  }
  if (engine && motionOn && !dialog.open && !booting) {
    engine.update(story);
    if (live) {
      const title = document.querySelector(".hero h1");
      // Fade only once the falling title reaches the platform's projected edge.
      const overlap =
        title.getBoundingClientRect().bottom - engine.platformScreenY();
      title.style.opacity = 1 - smooth(overlap, 0, innerHeight * 0.23);
    }
  }
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
    if (booting || heroRevealing) lenis.stop();
  }
}
function setLive(on) {
  const before = booting || heroRevealing ? 0 : story;
  live = on;
  body.classList.toggle("is-live", on);
  body.classList.toggle("is-static", !on);
  body.dataset.renderMode = on ? "live" : "static";
  if (!on) {
    powerCards.forEach(card=>{
      card.style.removeProperty('--power-y');
      card.style.opacity='';card.style.visibility='';card.inert=false;
      card.removeAttribute('aria-hidden');
    });
    opticsCards.forEach(card=>{
      card.style.removeProperty('--optics-y');
      card.style.opacity='';card.style.visibility='';card.inert=false;
      card.removeAttribute('aria-hidden');
    });
    worldCaptions.forEach(c=>{c.style.opacity='';c.style.transform='';c.removeAttribute('aria-hidden');});
    controlCards.forEach(card=>{
      card.style.removeProperty('--control-y');
      card.style.opacity='';card.style.visibility='';card.inert=false;
      card.removeAttribute('aria-hidden');
    });
    flightCards.forEach((card) => {
      card.style.removeProperty("--flight-x");
      card.style.removeProperty('--flight-focus');
      card.classList.remove('is-active');
      card.removeAttribute('aria-current');
      card.style.opacity = "";
      card.style.visibility = "";
      card.inert = false;
      card.removeAttribute("aria-hidden");
    });
    body.classList.remove("is-light");
    document.querySelector(".hero h1").style.opacity = "";
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
    top: on ? storyToScroll(before, anchors) : anchors[Math.round(before)],
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
  enginePromise = import("./js/scene.js?v=4.17.1")
    .then(({ createScene }) =>
      createScene({
        initialIntro: booting ? 0 : 1,
        onProgress: (p) => {
          const percent = Math.round(p * 100);
          document.querySelector("#load-progress").textContent = p
            ? percent + "%"
            : "";

        },
        onFailure: fallback,
      }),
    )
    .then((value) => {
      engine = value;
      engine.setFinish(preorder.selected.id);
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
        if (booting) introPlay();
        else engine.render(performance.now());
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
  motionOn = on;
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
function navigate(hash, instant = false) {
  const index = sections.findIndex((s) => "#" + s.id === hash);
  if (index < 0) return;
  if (heroRevealing) heroRevealEnd();
  if (booting) return;
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
  if (heroRevealing) heroRevealEnd();
  if (booting) return;
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
gsap.ticker.add((t, deltaMs) => {
  if (booting && !document.hidden) bootIntro.tick(deltaMs);
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
      if (lenis)
        lenis.scrollTo(storyToScroll(previous, anchors), { immediate: true });
      else window.scrollTo(0, storyToScroll(previous, anchors));
    }
    engine?.resize();
    ScrollTrigger.refresh();
  }, 140);
});
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
if (motionOn) {
  if (replayIntroOnLoad) introStart();
  loadScene().then(() => {
    if (location.hash) navigate(location.hash, true);
  });
} else if (location.hash)
  requestAnimationFrame(() => navigate(location.hash, true));
window.aerixInspect = () => ({
  ready: true,
  version: '4.17.1',
  motionOn,
  mobile: mobileQuery.matches,
  reduced: reducedQuery.matches,
  renderMode: body.dataset.renderMode,
  failed,
  story,
  controlCards: controlCardsAt(story),
  opticsCards: opticsCardsAt(story,mobileQuery.matches),
  flightWorlds: flightWorldsAt(story),
  anchors: [...anchors],
  explorerOpen: dialog.open,
  booting,
  heroRevealing,
  title: heroTitle.inspect(),
  introduction: bootIntro.inspect(),
  engine: engine?.inspect(),
});
window.aerixReady = true;

if (new URLSearchParams(location.search).has("qa"))
  window.aerixQA = {
    seek: (t) => {
      if (heroRevealing) heroRevealEnd();
      if (lenis)
        lenis.scrollTo(storyToScroll(clamp(t, 0, 8), anchors), {
          immediate: true,
        });
      else window.scrollTo(0, storyToScroll(clamp(t, 0, 8), anchors));
      updateStory(true);
    },
    introState: () => ({ booting, heroRevealing, ready: !!engine, ...bootIntro.inspect() }),
    replayIntro: () => {
      window.aerixQA.seek(0);
      introStart();
      if (engine) introPlay();
    },
    previewIntro: (seconds) => {
      if (!booting) introStart({ paused: true });
      bootIntro.preview(seconds);
    },
    replayTitle: () => heroRevealStart(),
    previewTitle: (seconds) => {
      if (!heroRevealing && !heroRevealStart({ paused: true })) return;
      heroTitle.preview(seconds);
    },
    capture: (name) => engine?.capture(name),
    inspectSurface: (options) => engine?.captureInspection(options),
    anchors: () => engine?.verifyFramingContract(),
    sequence: () => engine?.verifySequence(),
  };

// Local review controls are absent from the normal landing page.
if (new URLSearchParams(location.search).has("qa")) {
  const panel = document.createElement("form");
  panel.id = "review-tools";
  panel.innerHTML =
    '<label>Story <input aria-label="Story position" name="position" type="number" min="0" max="8" step=".01" value="0"></label><button>Seek</button><button type="button" data-intro>Replay intro</button><label>Intro <input aria-label="Intro time" name="introTime" type="number" min="0" max="5.4" step=".01" value="0"></label><button type="button" data-intro-preview>Preview intro</button><button type="button" data-title-replay>Replay title</button><label>Title <input aria-label="Title time" name="titleTime" type="number" min="0" max="3.18" step=".01" value="0"></label><button type="button" data-title-preview>Preview title</button><button type="button" data-check>Check render</button><button type="button" data-audit>Run checks</button><button type="button" data-poster="hero">Hero poster</button><button type="button" data-poster="sky">Sky poster</button><button type="button" data-poster="exploded">Layers poster</button><button type="button" data-poster="battery">Battery poster</button><button type="button" data-poster="computer">Computer poster</button><button type="button" data-poster="optics">Optics poster</button><output aria-label="Render diagnostics"></output>';
  document.body.append(panel);
  const povCheck=document.createElement('button');
  povCheck.type='button';povCheck.textContent='Check POV';
  povCheck.onclick=()=>{const data=window.aerixInspect();panel.querySelector('output').textContent=JSON.stringify({story:data.story,failed:data.failed,engineReady:data.engine?.ready,camera:data.engine?.camera,studies:data.engine?.studies,worlds:data.engine?.flightWorlds,backgroundSky:data.engine?.backgroundSky,finish:data.engine?.finish,roundedLens:povLensAt(story),portal:lensPortalAt(story),message:copyAt(story,6).alpha});};
  panel.append(povCheck);
  const finishReview=document.createElement('button');
  finishReview.type='button';finishReview.textContent='Finish review';
  finishReview.onclick=()=>{const url=new URL(location.href);url.searchParams.delete('qa');history.replaceState(null,'',url);panel.remove();delete window.aerixQA;};
  panel.append(finishReview);
  panel.addEventListener("submit", (e) => {
    e.preventDefault();
    window.aerixQA.seek(Number(panel.elements.position.value));
  });
  panel.querySelector("[data-intro]").addEventListener("click", () => {
    if (engine) window.aerixQA.replayIntro();
  });
  panel.querySelector("[data-intro-preview]").addEventListener("click", () => {
    window.aerixQA.previewIntro(Math.min(BOOT_DURATION, Number(panel.elements.introTime.value)));
  });
  panel.querySelector("[data-title-replay]").addEventListener("click", () => {
    window.aerixQA.replayTitle();
  });
  panel.querySelector("[data-title-preview]").addEventListener("click", () => {
    window.aerixQA.previewTitle(Number(panel.elements.titleTime.value));
  });
  panel.querySelectorAll("[data-poster]").forEach((button) =>
    button.addEventListener("click", () => {
      const name = button.dataset.poster,
        data = window.aerixQA.capture(name);
      if (!data) return;
      const link = document.createElement("a");
      link.href = data;
      link.download = `aerix-v4-${name}.png`;
      link.click();
    }),
  );
  panel.querySelector("[data-audit]").addEventListener("click", () => {
    panel.querySelector("output").textContent = JSON.stringify(
      window.aerixQA.sequence(),
    );
  });
  panel.querySelector("[data-check]").addEventListener("click", () => {
    const data = window.aerixInspect();
    panel.querySelector("output").textContent = JSON.stringify({
      story: data.story,
      heroRevealing: data.heroRevealing,
      title: data.title,
      introduction: data.introduction,
      mode: data.renderMode,
      failed: data.failed,
      solidMaterialViolations: data.engine?.solidMaterialViolations,
      batteryFinishes: data.engine?.batteryFinishes,
      motherboardFinishes: data.engine?.motherboardFinishes,
      studies: data.engine?.studies,
      anatomy: data.engine?.anatomy,
      camera: data.engine?.camera,
      drawCalls: data.engine?.drawCalls,
      triangles: data.engine?.triangles,
      renderMs: data.engine?.averageRenderSubmitMs,
    });
  });
}
