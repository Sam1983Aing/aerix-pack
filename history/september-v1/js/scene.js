import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { DRACOLoader } from "three/addons/loaders/DRACOLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { OrbitControls } from "../vendor/three/addons/OrbitControls.js";
import { sampleStory, VIEWS, explorerPose, lerp } from "./story.js";
const ROOTS = {
  battery: "BATTERY_ROOT",
  thermal: "THERMAL_ROOT",
  computer: "FLIGHT_COMPUTER_ROOT",
  tray: "INTERNAL_SUPPORT_ROOT",
  optics: "CAMERA_GIMBAL_ROOT",
  chassis: "INTERIOR_CHASSIS_ROOT",
};
const CLIPS = {
  fold: "Fold_arms_and_blades",
  body: "Body_reveal",
  battery: "Battery_reveal",
  optics: "Optics_reveal",
  thermal: "Thermal_detail",
  computer: "Computer_detail",
  tray: "Tray_detail",
};
export async function createScene({
  onProgress = () => {},
  onFailure = () => {},
} = {}) {
  const mount = document.querySelector("#canvas-mount"),
    stage = document.querySelector("#visual-stage");
  const renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: true,
    powerPreference: "high-performance",
  });
  renderer.setPixelRatio(
    Math.min(devicePixelRatio, innerWidth < 761 ? 1.25 : 1.6),
  );
  renderer.setClearColor(0x000000, 0);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.08;
  mount.append(renderer.domElement);
  const camera = new THREE.PerspectiveCamera(34, 1, 0.004, 10),
    scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer),
    room = new RoomEnvironment();
  scene.environment = pmrem.fromScene(room, 0.04).texture;
  scene.environmentIntensity = 1;
  scene.environmentRotation.y = 0.35;
  room.dispose();
  pmrem.dispose();
  scene.add(new THREE.HemisphereLight(0xeceee8, 0x323c37, 0.26));
  const key = new THREE.DirectionalLight(0xffedda, 2.6);
  key.position.set(0.45, 0.65, 0.8);
  scene.add(key);
  const fill = new THREE.DirectionalLight(0xb6c8d8, 0.35);
  fill.position.set(-0.5, 0.1, 0.4);
  scene.add(fill);
  const rim = new THREE.DirectionalLight(0xe6e7de, 2.1);
  rim.position.set(-0.5, 0.45, -0.55);
  scene.add(rim);
  const draco = new DRACOLoader();
  draco.setDecoderPath(new URL("../vendor/draco/", import.meta.url).href);
  draco.setWorkerLimit(2);
  const loader = new GLTFLoader().setDRACOLoader(draco);
  let loaded;
  try {
    loaded = await new Promise((resolve, reject) =>
      loader.load(
        new URL("../assets/aerix-v01.glb", import.meta.url).href,
        resolve,
        (e) => onProgress(e.total ? e.loaded / e.total : 0),
        reject,
      ),
    );
  } catch (error) {
    draco.dispose();
    renderer.dispose();
    renderer.domElement.remove();
    scene.environment.dispose();
    throw error;
  }
  draco.dispose();
  const model = loaded.scene;
  const center = new THREE.Box3()
    .setFromObject(model)
    .getCenter(new THREE.Vector3());
  model.position.sub(center);
  scene.add(model);
  model.updateMatrixWorld(true);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enabled = false;
  controls.enableDamping = true;
  controls.dampingFactor = 0.1;
  controls.minDistance = 0.04;
  controls.maxDistance = 1.8;
  controls.zoomSpeed = 0.65;
  controls.enablePan = true;
  const meshes = [],
    materialCache = new Map(),
    mixers = {};
  const categoryOf = (o) => {
    for (let n = o; n; n = n.parent) {
      for (const [key, name] of Object.entries(ROOTS))
        if (n.name === name) return key;
    }
    return "exterior";
  };
  model.traverse((o) => {
    if (!o.isMesh) return;
    const category = categoryOf(o);
    const src = Array.isArray(o.material) ? o.material : [o.material];
    o.material = src.map((m) => {
      const key = m.uuid + category;
      if (!materialCache.has(key)) {
        const q = m.clone();
        q.userData.baseOpacity = m.opacity;
        q.userData.baseTransparent = m.transparent;
        q.userData.baseDepthWrite = m.depthWrite;
        for (const prop of [
          "map",
          "normalMap",
          "roughnessMap",
          "metalnessMap",
          "aoMap",
        ])
          if (q[prop])
            q[prop].anisotropy = Math.min(
              8,
              renderer.capabilities.getMaxAnisotropy(),
            );
        if (/laser etched|silkscreen|marking/i.test(q.name)) {
          q.polygonOffset = true;
          q.polygonOffsetFactor = -1;
          q.polygonOffsetUnits = -1;
        }
        materialCache.set(key, q);
      }
      return materialCache.get(key);
    });
    if (o.material.length === 1) o.material = o.material[0];
    meshes.push({ o, category });
  });
  for (const [key, name] of Object.entries(CLIPS)) {
    const clip = loaded.animations.find((c) => c.name === name);
    if (!clip) throw new Error("Missing clip " + name);
    const mixer = new THREE.AnimationMixer(model),
      action = mixer.clipAction(clip);
    action.setLoop(THREE.LoopOnce, 1);
    action.clampWhenFinished = true;
    action.play();
    mixers[key] = { mixer, action, duration: clip.duration };
  }
  let dirty = true,
    lastT = -1,
    active = true,
    exploring = false,
    lastState = null,
    frames = 0,
    lastRender = 0;
  const timings = [],
    target = new THREE.Vector3();
  const animatedNames = [
    ...new Set(
      loaded.animations.flatMap((c) =>
        c.tracks.map((t) => t.name.replace(/\.[^.]+$/, "")),
      ),
    ),
  ];
  function pose(state) {
    for (const [key, { mixer, action, duration }] of Object.entries(mixers)) {
      action.enabled = true;
      action.paused = false;
      mixer.setTime((state[key] || 0) * duration);
    }
    model.updateMatrixWorld(true);
  }
  function visibility(weights) {
    for (const { o, category } of meshes) {
      const w = weights[category] ?? 1;
      o.visible = w > 0.015;
      for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
        const transparent = m.userData.baseTransparent || w < 0.999;
        if (m.transparent !== transparent) {
          m.transparent = transparent;
          m.needsUpdate = true;
        }
        m.opacity = m.userData.baseOpacity * w;
        m.depthWrite = w > 0.999 ? m.userData.baseDepthWrite : false;
      }
    }
  }
  function focus(name) {
    const root = name === "whole" ? model : model.getObjectByName(ROOTS[name]);
    return new THREE.Box3().setFromObject(root).getCenter(new THREE.Vector3());
  }
  function setCamera(a, b, v, pullback = 0) {
    target.copy(focus(a.focus)).lerp(focus(b.focus), v);
    const dir = new THREE.Vector3()
      .fromArray(a.dir)
      .lerp(new THREE.Vector3().fromArray(b.dir), v)
      .normalize();
    camera.position
      .copy(target)
      .addScaledVector(
        dir,
        (lerp(a.distance, b.distance, v) + pullback) *
          Math.max(1, 1.6 / camera.aspect),
      );
    camera.lookAt(target);
    const rect = mount.getBoundingClientRect();
    camera.setViewOffset(
      rect.width,
      rect.height,
      -rect.width * lerp(a.x, b.x, v),
      0,
      rect.width,
      rect.height,
    );
    controls.target.copy(target);
    camera.updateMatrixWorld(true);
  }
  function labels(alpha) {
    const container = document.querySelector("#model-labels");
    container.style.opacity = String(alpha);
    if (alpha < 0.01) return;
    const rect = mount.getBoundingClientRect();
    for (const [key, name] of Object.entries(ROOTS)) {
      const el = container.querySelector(`[data-label="${key}"]`);
      if (!el) continue;
      const p = focus(key).project(camera);
      el.style.transform = `translate(${(p.x * 0.5 + 0.5) * rect.width + 65}px,${(-p.y * 0.5 + 0.5) * rect.height}px)`;
    }
  }
  function update(t) {
    if (exploring || t === lastT) return;
    lastT = t;
    lastState = sampleStory(t);
    pose(lastState.pose);
    visibility(lastState.weights);
    setCamera(
      VIEWS[lastState.a],
      VIEWS[lastState.b],
      lastState.cameraV,
      lastState.cameraPullback,
    );
    labels(lastState.labelAlpha);
    dirty = true;
  }
  function resize() {
    const rect = mount.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    renderer.setSize(rect.width, rect.height, false);
    camera.aspect = rect.width / rect.height;
    camera.updateProjectionMatrix();
    if (exploring) {
      camera.clearViewOffset();
      controls.update();
    } else {
      const t = lastT;
      lastT = -1;
      update(Math.max(0, t));
    }
    dirty = true;
  }
  function render(now) {
    if (!active || document.hidden) return;
    if (exploring) {
      controls.update();
      dirty = true;
    }
    if (!dirty) return;
    const start = performance.now();
    renderer.render(scene, camera);
    timings.push(performance.now() - start);
    if (timings.length > 240) timings.shift();
    lastRender = now;
    frames++;
    dirty = false;
  }
  function inspect() {
    return {
      ready: true,
      exploring,
      t: lastT,
      state: lastState,
      frames,
      drawCalls: renderer.info.render.calls,
      triangles: renderer.info.render.triangles,
      textures: renderer.info.memory.textures,
      geometries: renderer.info.memory.geometries,
      averageRenderSubmitMs:
        timings.reduce((a, b) => a + b, 0) / Math.max(1, timings.length),
      matrices: Object.fromEntries(
        animatedNames
          .filter((n) => model.getObjectByName(n))
          .map((n) => [n, model.getObjectByName(n).matrixWorld.toArray()]),
      ),
      camera: { position: camera.position.toArray(), target: target.toArray() },
      bounds: new THREE.Box3()
        .setFromObject(model)
        .getSize(new THREE.Vector3())
        .toArray(),
    };
  }
  function explore(name) {
    exploring = true;
    active = true;
    controls.enabled = true;
    const state = explorerPose(name);
    pose(state.pose);
    visibility(state.weights);
    camera.clearViewOffset();
    target.copy(focus(state.view.focus));
    camera.position
      .copy(target)
      .addScaledVector(
        new THREE.Vector3().fromArray(state.view.dir).normalize(),
        state.view.distance * Math.max(0.86, 1.1 / camera.aspect),
      );
    controls.target.copy(target);
    controls.update();
    labels(0);
    dirty = true;
  }
  function close() {
    exploring = false;
    controls.enabled = false;
    lastT = -1;
    dirty = true;
  }
  renderer.domElement.tabIndex = 0;
  renderer.domElement.setAttribute(
    "aria-label",
    "Interactive AERIX drone. Arrow keys rotate; plus and minus zoom.",
  );
  renderer.domElement.addEventListener("keydown", (e) => {
    if (!exploring) return;
    const delta = camera.position.clone().sub(controls.target);
    if (["ArrowLeft", "ArrowRight"].includes(e.key))
      delta.applyAxisAngle(
        new THREE.Vector3(0, 1, 0),
        e.key === "ArrowLeft" ? 0.12 : -0.12,
      );
    else if (["ArrowUp", "ArrowDown"].includes(e.key)) {
      const axis = new THREE.Vector3()
        .crossVectors(delta, new THREE.Vector3(0, 1, 0))
        .normalize();
      delta.applyAxisAngle(axis, e.key === "ArrowUp" ? 0.1 : -0.1);
    } else if (["+", "=", "-"].includes(e.key))
      delta.multiplyScalar(e.key === "-" ? 1.1 : 0.9);
    else return;
    e.preventDefault();
    camera.position.copy(controls.target).add(delta);
    controls.update();
    dirty = true;
  });
  renderer.domElement.addEventListener("webglcontextlost", (e) => {
    e.preventDefault();
    active = false;
    onFailure();
  });
  resize();
  update(0);
  await renderer.compileAsync(scene, camera);
  return {
    update,
    resize,
    render,
    inspect,
    explore,
    close,
    setActive(v) {
      active = v;
      dirty = true;
    },
    dispose() {
      controls.dispose();
      renderer.dispose();
      scene.environment.dispose();
    },
  };
}
