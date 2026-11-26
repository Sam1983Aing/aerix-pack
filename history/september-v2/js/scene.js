import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { DRACOLoader } from "three/addons/loaders/DRACOLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { OrbitControls } from "../vendor/three/addons/OrbitControls.js";
import {
  sampleStory,
  VIEWS,
  explorerPose,
  lerp,
  smooth,
} from "./story.js?v=2.2";
import { ROOTS, ANCHORS, MODEL_OFFSET } from "./anchors.js";
import { sampleHover, FLIGHT_TUNING } from "./flight.js?v=2.2";
import {
  createAtmosphere,
  createPlatform,
  createRotorDisc,
} from "./effects.js?v=2.1";
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
    Math.min(devicePixelRatio, innerWidth < 761 ? 1.5 : 2),
  );
  renderer.setClearColor(0x000000, 0);
  renderer.autoClear = false;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.08;
  mount.append(renderer.domElement);
  const camera = new THREE.PerspectiveCamera(34, 1, 0.001, 10),
    scene = new THREE.Scene();
  const atmosphere = createAtmosphere(),
    platform = createPlatform();
  scene.add(platform.group);
  scene.fog = new THREE.FogExp2(0xa9bbae, 0);
  const pmrem = new THREE.PMREMGenerator(renderer),
    room = new RoomEnvironment();
  room.children[1].material.color.set(0x929b98);
  // Broad studio cards add controlled highlight ribbons without changing approved materials.
  for (const [position, scale, intensity] of [
    [[-4, 5, 3], [3.5, 1.0, 1], 5],
    [[3, 3, -4], [0.75, 4.5, 1], 4],
  ]) {
    const card = new THREE.Mesh(
      new THREE.PlaneGeometry(1, 1),
      new THREE.MeshBasicMaterial({
        color: new THREE.Color().setScalar(intensity),
        side: THREE.DoubleSide,
      }),
    );
    card.position.fromArray(position);
    card.scale.fromArray(scale);
    card.lookAt(0, 0, 0);
    room.add(card);
  }
  scene.environment = pmrem.fromScene(room, 0.025).texture;
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
        new URL("../assets/aerix-quality-v02.glb", import.meta.url).href,
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
  model.position.fromArray(MODEL_OFFSET);
  const flightRig = new THREE.Group();
  flightRig.name = "V2_FLIGHT_RIG";
  flightRig.add(model);
  scene.add(flightRig);
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
    let blade = false;
    for (let n = o; n; n = n.parent)
      if (n.name.startsWith("BLADE_FOLD_")) blade = true;
    const src = Array.isArray(o.material) ? o.material : [o.material];
    o.material = src.map((m) => {
      const key = m.uuid + category + blade;
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
    meshes.push({ o, category, blade });
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
  const rotors = ["FL", "FR", "RL", "RR"].map((suffix, i) => {
    const root = model.getObjectByName("PROPELLER_" + suffix),
      spin = new THREE.Group();
    spin.name = "V2_SPIN_" + suffix;
    const children = [...root.children];
    root.add(spin);
    for (const child of children) spin.add(child);
    const disc = createRotorDisc();
    root.add(disc);
    return { spin, disc, sign: i === 0 || i === 3 ? 1 : -1 };
  });
  let intro = 1,
    pointerX = 0,
    pointerY = 0,
    cinematic = true;
  let flightClock = 0,
    previousFrame = null,
    previousFlightT = 0,
    drive = 0;
  const easedPointer = { x: 0, y: 0 };
  let hoverState = sampleHover(0, 0, easedPointer, 0);
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
  function visibility(weights, alpha = 1, speed = 0) {
    for (const { o, category, blade } of meshes) {
      const w =
        (weights[category] ?? 1) *
        alpha *
        (blade ? 1 - smooth(speed, 0.12, 0.68) : 1);
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
    const anchor = ANCHORS[name] || ANCHORS.whole;
    const root = anchor.root ? model.getObjectByName(anchor.root) : flightRig;
    return root.localToWorld(new THREE.Vector3().fromArray(anchor.point));
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
      -rect.height * lerp(a.y || 0, b.y || 0, v),
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
      el.style.transform = `translate(${(p.x * 0.5 + 0.5) * rect.width + 100}px,${(-p.y * 0.5 + 0.5) * rect.height}px)`;
    }
  }
  function update(t) {
    if (exploring || t === lastT) return;
    lastT = t;
    lastState = sampleStory(t);
    flightRig.position.set(
      lastState.flight.x,
      lastState.lift,
      lastState.flight.z,
    );
    flightRig.rotation.set(
      lastState.flight.pitch,
      lastState.flight.yaw,
      lastState.flight.roll,
    );
    pose(lastState.pose);
    visibility(
      lastState.weights,
      lastState.a === 6 ? 1 : lastState.modelAlpha,
      lastState.rotors,
    );
    scene.fog.density = 0;
    key.intensity = 2.6 - 0.8 * lastState.sky;
    scene.environmentIntensity = 1 - 0.12 * lastState.sky;
    platform.update(lastState.platformAlpha, lastState.lift);
    flightRig.visible = lastState.modelAlpha > 0.01;
    atmosphere.uniforms.uT.value = t;
    atmosphere.uniforms.uSky.value = lastState.sky;
    atmosphere.uniforms.uGlass.value = lastState.glass;
    setCamera(
      { ...VIEWS[lastState.a], x: VIEWS[lastState.a].x + lastState.viewXBoost },
      { ...VIEWS[lastState.b], x: VIEWS[lastState.b].x + lastState.viewXBoost },
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
    atmosphere.uniforms.uAspect.value = camera.aspect;
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
    const seconds = now / 1000;
    const dt =
      previousFrame === null
        ? 1 / 60
        : Math.max(0, Math.min(0.05, (now - previousFrame) / 1000));
    previousFrame = now;
    if (exploring) {
      controls.update();
      dirty = true;
    } else if (lastState && cinematic && intro === 1) {
      flightClock += dt;
      const delta = lastState.t - previousFlightT;
      const impulse =
        Math.abs(delta) > 0.3 || dt === 0
          ? 0
          : THREE.MathUtils.clamp(delta / dt / 0.9, -1, 1);
      drive = lerp(
        drive,
        impulse,
        1 - Math.exp(-dt / FLIGHT_TUNING.responseSeconds),
      );
      previousFlightT = lastState.t;
      const pointerBlend = 1 - Math.exp(-dt / 0.35);
      easedPointer.x = lerp(easedPointer.x, pointerX, pointerBlend);
      easedPointer.y = lerp(easedPointer.y, pointerY, pointerBlend);
      hoverState = sampleHover(
        flightClock,
        lastState.flight.airborne,
        easedPointer,
        drive,
      );
      flightRig.position.set(
        lastState.flight.x + hoverState.x,
        lastState.lift + hoverState.y,
        lastState.flight.z + hoverState.z,
      );
      flightRig.rotation.set(
        lastState.flight.pitch + hoverState.pitch,
        lastState.flight.yaw + hoverState.yaw,
        lastState.flight.roll + hoverState.roll,
      );
      for (const { spin, disc, sign } of rotors) {
        spin.rotation.y = seconds * lastState.rotors * 58 * sign;
        disc.visible =
          lastState.rotors > 0.01 && lastState.weights.exterior > 0.01;
        disc.material.uniforms.uSpeed.value =
          lastState.rotors * lastState.weights.exterior * lastState.modelAlpha;
        disc.material.uniforms.uTime.value = seconds * sign;
      }
      atmosphere.uniforms.uTime.value = seconds;
      atmosphere.uniforms.uPointer.value.set(pointerX, pointerY);
      dirty = true;
    }
    if (!dirty) return;
    const start = performance.now();
    renderer.clear();
    renderer.render(atmosphere.scene, atmosphere.camera);
    renderer.clearDepth();
    renderer.render(scene, camera);
    timings.push(performance.now() - start);
    if (timings.length > 240) timings.shift();
    lastRender = now;
    frames++;
    dirty = false;
  }
  function setIntro(value) {
    intro = value;
    const light = smooth(value, 0.02, 0.42);
    atmosphere.uniforms.uBoot.value = 0.2 + 0.8 * light;
    key.intensity = 0.035 + 2.565 * light;
    fill.intensity = 0.02 + 0.33 * light;
    rim.intensity = 0.03 + 2.07 * light;
    scene.environmentIntensity = 0.03 + 0.97 * light;
    if (value < 1) {
      flightRig.position.set(0, 0, 0);
      flightRig.rotation.set(0, 0, 0);
      flightRig.updateMatrixWorld(true);
      setCamera(
        { focus: "lens", dir: [0, 0.025, 1], distance: 0.35, x: 0, y: 0 },
        VIEWS[0],
        smooth(value, 0.4, 1),
      );
    } else {
      lastT = -1;
      update(lastState?.t || 0);
    }
    dirty = true;
  }
  function inspect() {
    return {
      ready: true,
      version: 2,
      intro,
      anchorContract: ANCHORS,
      modelOffset: MODEL_OFFSET,
      flightMotion: {
        path: lastState?.flight,
        hover: hoverState,
        drive,
        clock: flightClock,
        position: flightRig.position.toArray(),
        rotation: flightRig.rotation.toArray().slice(0, 3),
      },
      rotors: rotors.map(({ disc, spin }) => ({
        blur: disc.visible,
        speed: disc.material.uniforms.uSpeed.value,
        angle: spin.rotation.y,
      })),
      bladeVisible: meshes.filter((m) => m.blade && m.o.visible).length,
      localMatrices: Object.fromEntries(
        animatedNames
          .filter((n) => model.getObjectByName(n))
          .map((n) => [n, model.getObjectByName(n).matrix.toArray()]),
      ),
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
    renderer.domElement.tabIndex = 0;
    const state = explorerPose(name);
    flightRig.visible = true;
    flightRig.position.set(0, 0, 0);
    flightRig.rotation.set(0, 0, 0);
    platform.group.visible = false;
    scene.fog.density = 0;
    atmosphere.uniforms.uExplore.value = 1;
    atmosphere.uniforms.uBoot.value = 1;
    key.intensity = 2.6;
    fill.intensity = 0.35;
    rim.intensity = 2.1;
    scene.environmentIntensity = 1;
    rotors.forEach(({ spin, disc }) => {
      spin.rotation.y = 0;
      disc.visible = false;
    });
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
    renderer.domElement.tabIndex = -1;
    atmosphere.uniforms.uExplore.value = 0;
    controls.enabled = false;
    lastT = -1;
    dirty = true;
  }
  renderer.domElement.tabIndex = -1;
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
    setIntro,
    setPointer(x, y) {
      pointerX = x;
      pointerY = y;
    },
    setCinematic(v) {
      cinematic = v;
      dirty = true;
    },
    resize,
    render,
    inspect,
    explore,
    close,
    setActive(v) {
      active = v;
      dirty = true;
    },
    verifyFramingContract() {
      const t = lastT;
      lastT = -1;
      update(t);
      const before = [...camera.position.toArray(), ...target.toArray()];
      const geometries = [...new Set(meshes.map(({ o }) => o.geometry))];
      const boxes = geometries.map((g) => g.boundingBox?.clone() || null);
      for (const g of geometries) {
        g.computeBoundingBox();
        g.boundingBox.expandByScalar(10);
      }
      lastT = -1;
      update(t);
      const after = [...camera.position.toArray(), ...target.toArray()];
      geometries.forEach((g, i) => (g.boundingBox = boxes[i]));
      return {
        stable: before.every((v, i) => Math.abs(v - after[i]) < 1e-12),
        before,
        after,
        expandedGeometryCount: geometries.length,
      };
    },
    // Deterministic native renders for the ?qa surface-fidelity review.
    captureInspection({
      pose: name = "flight",
      closed = false,
      focus: anchor = "whole",
      point,
      dir = [0, 0, 1],
      distance = 0.5,
    } = {}) {
      const t = lastT,
        ratio = renderer.getPixelRatio();
      explore(name);
      if (closed) pose({});
      controls.enabled = false;
      renderer.setPixelRatio(1);
      renderer.setSize(1200, 1000, false);
      camera.aspect = 1.2;
      camera.clearViewOffset();
      camera.updateProjectionMatrix();
      target.copy(point ? new THREE.Vector3().fromArray(point) : focus(anchor));
      camera.position
        .copy(target)
        .addScaledVector(
          new THREE.Vector3().fromArray(dir).normalize(),
          distance,
        );
      camera.lookAt(target);
      model.updateMatrixWorld(true);
      renderer.clear();
      renderer.render(atmosphere.scene, atmosphere.camera);
      renderer.clearDepth();
      renderer.render(scene, camera);
      const data = renderer.domElement.toDataURL("image/png");
      renderer.setPixelRatio(ratio);
      close();
      resize();
      lastT = -1;
      update(t);
      return data;
    },
    capture(name) {
      const t = lastT,
        ratio = renderer.getPixelRatio();
      explore("flight");
      controls.enabled = false;
      renderer.setPixelRatio(1);
      renderer.setSize(1800, 1350, false);
      camera.aspect = 4 / 3;
      camera.clearViewOffset();
      camera.updateProjectionMatrix();
      const sky = name === "sky";
      target.set(0, sky ? 0 : -0.02, 0);
      camera.position
        .copy(target)
        .addScaledVector(
          new THREE.Vector3(
            ...(sky ? [-0.52, 0.27, -1] : [0.27, 0.34, 1]),
          ).normalize(),
          sky ? 0.92 : 0.97,
        );
      camera.lookAt(target);
      platform.update(sky ? 0 : 1, 0);
      visibility(explorerPose("flight").weights, 1, sky ? 1 : 0);
      for (const { disc } of rotors) {
        disc.visible = sky;
        disc.material.uniforms.uSpeed.value = 1;
      }
      key.intensity = sky ? 1.8 : 2.6;
      renderer.clear();
      renderer.render(scene, camera);
      const data = renderer.domElement.toDataURL("image/png");
      renderer.setPixelRatio(ratio);
      close();
      resize();
      lastT = -1;
      update(t);
      return data;
    },
    dispose() {
      atmosphere.dispose();
      platform.dispose();
      controls.dispose();
      renderer.dispose();
      renderer.domElement.remove();
      scene.environment.dispose();
    },
  };
}
