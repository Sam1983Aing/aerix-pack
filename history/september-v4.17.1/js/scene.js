import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { DRACOLoader } from "three/addons/loaders/DRACOLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { OrbitControls } from "../vendor/three/addons/OrbitControls.js";
import {
  sampleStory,
  explorerPose,
  lerp,
  smooth,
  performanceFraming,
} from "./story.js?v=4.17.1";
import { ROOTS, ANCHORS, MODEL_OFFSET } from "./anchors.js";
import {FINISHES,DEFAULT_FINISH} from './finishes.js?v=4.16.1';
import { createAnatomy } from "./anatomy.js?v=4.8.4";
import {createPerformance,PERFORMANCE_PARTS} from './performance.js?v=4.12';
import { sampleHover, FLIGHT_TUNING } from "./flight.js?v=4.14";
import {
  createAtmosphere,
  createPlatform,
  createRotorDisc,
} from "./effects.js?v=4.17";
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
  initialIntro = 1,
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
  // Atmosphere sits behind the HTML; opaque geometry sits in front of it.
  // This preserves real occlusion without changing any source material alpha.
  const background = new THREE.WebGLRenderer({
    alpha: false,
    antialias: false,
  });
  background.setPixelRatio(Math.min(devicePixelRatio, 1.5));
  background.domElement.id = "atmosphere-canvas";
  background.domElement.setAttribute("aria-hidden", "true");
  document.body.prepend(background.domElement);
  const camera = new THREE.PerspectiveCamera(34, 1, 0.001, 10),
    scene = new THREE.Scene();
  const atmosphere = createAtmosphere(),
    platform = createPlatform();
  scene.add(platform.group);
  // Transmission needs a real background in its offscreen buffer. Draw this
  // backdrop only into that buffer, leaving the foreground canvas transparent.
  const transmissionBackdrop = atmosphere.scene.children[0].clone();
  transmissionBackdrop.material = transmissionBackdrop.material.clone();
  transmissionBackdrop.material.uniforms = atmosphere.uniforms;
  // The atmosphere is authored in display space; the transmission buffer is linear.
  transmissionBackdrop.material.fragmentShader =
    transmissionBackdrop.material.fragmentShader.replace(
      "gl_FragColor=vec4(col,1.);",
      "gl_FragColor=vec4(pow(max(col,vec3(0.)),vec3(2.2)),1.);",
    );
  transmissionBackdrop.frustumCulled = false;
  transmissionBackdrop.renderOrder = -1000;
  transmissionBackdrop.onBeforeRender = (r) => {
    transmissionBackdrop.material.colorWrite = r.getRenderTarget() !== null;
  };
  scene.add(transmissionBackdrop);
  scene.fog = new THREE.FogExp2(0xafc9e0, 0);
  const pmrem = new THREE.PMREMGenerator(renderer),
    room = new RoomEnvironment();
  room.children[1].material.color.set(0x969ead);
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
  const hemisphere = new THREE.HemisphereLight(0xeaf3ff, 0x222e42, 0.26);
  scene.add(hemisphere);
  const key = new THREE.DirectionalLight(0xf0f5ff, 2.6);
  key.position.set(0.45, 0.65, 0.8);
  scene.add(key);
  const fill = new THREE.DirectionalLight(0xb6c8d8, 0.35);
  fill.position.set(-0.5, 0.1, 0.4);
  scene.add(fill);
  const rim = new THREE.DirectionalLight(0xcce5ff, 2.1);
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
        new URL("../assets/aerix-flightcore-finish-v32.glb?v=2", import.meta.url).href,
        resolve,
        (e) => onProgress(e.total ? e.loaded / e.total : 0),
        reject,
      ),
    );
  } catch (error) {
    draco.dispose();
    renderer.dispose();
    renderer.domElement.remove();
    background.dispose();
    background.domElement.remove();
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
        // The foil gets a restrained studio reflection so the pressed laminate
        // remains legible. Explicit binding scopes this to the battery material;
        // scene-wide lighting and every other component retain their V4 setup.
        if (category === "battery" && /laminated aluminum foil/.test(q.name)) {
          q.envMap = scene.environment;
          q.envMapRotation.copy(scene.environmentRotation);
          q.envMapIntensity = 0.22;
        }
        // Matte solder mask and molded packages have quieter reflections than
        // the metallic airframe. Scope this look development to the computer.
        if (category === "computer" && /^V32/.test(q.name)) {
          const intensity = /deep green soldermask/.test(q.name)
            ? 0.42
            : /molded semiconductor|connector polymer|isolation elastomer|silicone/.test(q.name)
              ? 0.38
              : /satin bead blasted aluminum/.test(q.name)
                ? 0.5
                : null;
          if (intensity !== null) {
            q.envMap = scene.environment;
            q.envMapRotation.copy(scene.environmentRotation);
            q.envMapIntensity = intensity;
          }
        }
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
  const shellMaterials=[...materialCache.values()].filter(m=>['V25 baked titanium body','V22 satin titanium front edge'].includes(m.name));
  const finishBaselines=[...materialCache.values()].map(m=>({m,color:m.color?.clone(),roughness:m.roughness,metalness:m.metalness,maps:['map','normalMap','roughnessMap','metalnessMap','aoMap'].map(k=>m[k])}));
  let selectedFinish=DEFAULT_FINISH;
  // Restore the original color of each material separately, including the rim.
  const shellTargets=shellMaterials.map(m=>({m,original:m.color.clone(),target:m.color.clone()}));
  function setFinish(id){
    selectedFinish=FINISHES.find(f=>f.id===id)||DEFAULT_FINISH;
    for(const {original,target} of shellTargets){
      if(selectedFinish.original)target.copy(original);
      else target.set(selectedFinish.color);
    }
    dirty=true;
  }
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
      o.visible =
        (weights[category] ?? 1) > 0.5 &&
        alpha > 0.5 &&
        (!blade || speed < 0.4);
      // Source optical glass and decals keep their original settings. Solid
      // parts always retain their depth buffer and never become see-through.
      for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
        m.opacity = m.userData.baseOpacity;
        m.depthWrite = m.userData.baseDepthWrite;
      }
    }
  }
  const presentation = new THREE.Vector3(0, 0.3, 0);
  function createStudy(category) {
    const object = model.clone(true),
      rig = new THREE.Group();
    rig.name = "V3_STUDY_" + category;
    rig.add(object);
    scene.add(rig);
    object.traverse((o) => {
      if (o.isMesh)
        o.visible =
          categoryOf(o) === category && !o.name.startsWith("V2_ROTOR");
    });
    const tracks = Object.fromEntries(
      Object.entries(CLIPS).map(([k, name]) => {
        const clip = loaded.animations.find((c) => c.name === name);
        const mixer = new THREE.AnimationMixer(object),
          action = mixer.clipAction(clip);
        action.setLoop(THREE.LoopOnce, 1);
        action.clampWhenFinished = true;
        action.play();
        mixer.setTime(0);
        return [k, { mixer, action, duration: clip.duration }];
      }),
    );
    rig.visible = false;
    return { object, rig, tracks };
  }
  const studies = Object.fromEntries(
    ["battery", "computer", "optics"].map((k) => [k, createStudy(k)]),
  );
  // Preserve every finish. Only the illumination contribution changes on boot.
  const introMaterials = new Map();
  scene.traverse((o) => {
    if (!o.material) return;
    for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
      if (introMaterials.has(m)) continue;
      introMaterials.set(m, {
        env: m.envMap ? m.envMapIntensity : null,
        emissive: m.emissiveIntensity,
        basicColor: m.isMeshBasicMaterial ? m.color.clone() : null,
      });
    }
  });
  const storyLight = { key: 2.45, rim: 2.1, environment: .95 };
  function updateStudies(states) {
    for (const [name, study] of Object.entries(studies)) {
      const state = states[name];
      study.rig.visible = !!state?.visible;
      for (const [k, { mixer, action, duration }] of Object.entries(
        study.tracks,
      )) {
        action.enabled = true;
        action.paused = false;
        mixer.setTime(
          duration * (k === "body" ? 1 : k === name ? state.progress : 0),
        );
      }
      study.rig.position.set(0, 0, 0);
      study.rig.updateMatrixWorld(true);
      const anchor = ANCHORS[name];
      const point = study.object
        .getObjectByName(anchor.root)
        .localToWorld(new THREE.Vector3().fromArray(anchor.point));
      study.rig.position.copy(presentation).sub(point);
      study.rig.position.y += state.y;
      study.rig.updateMatrixWorld(true);
    }
  }
  function focus(name) {
    if (name === "presentation") return presentation.clone();
    if (name === "approach") return new THREE.Vector3(0,.26,0);
    if (name === "landing") return new THREE.Vector3(0,0,0);
    if (name === "opticalPortal")
      return studies.optics.object
        .getObjectByName(ROOTS.optics)
        .localToWorld(new THREE.Vector3().fromArray(ANCHORS.lens.point));
    const anchor = ANCHORS[name] || ANCHORS.whole;
    const root = anchor.root ? model.getObjectByName(anchor.root) : flightRig;
    return root.localToWorld(new THREE.Vector3().fromArray(anchor.point));
  }
  function setCamera(a, b, v, pullback = 0, direction = null) {
    target.copy(focus(a.focus)).lerp(focus(b.focus), v);
    const dir = new THREE.Vector3()
      .fromArray(direction || a.dir)
      .lerp(new THREE.Vector3().fromArray(direction || b.dir), v)
      .normalize();
    if (direction) dir.fromArray(direction);
    const phonePortrait =
      !exploring && camera.aspect < 0.8
        ? 1 - (lastState?.flight.angularFreedom ?? 1)
        : 0;
    // All three phone slots are reserved from the first reveal. Keep the lens
    // above that stack even before the second card moves the desktop camera up.
    const distance = lerp(a.distance, b.distance, v) + pullback;
    const closePortrait = smooth(lastT,1.39,1.57)*(1-smooth(lastT,1.67,1.98));
    const portraitDistance = lerp(distance, Math.max(distance, lerp(.94,.84,closePortrait)), phonePortrait);
    const phoneFlight = !exploring && camera.aspect < .8
      ? smooth(lastT,6.66,7)*(1-smooth(lastT,7.43,7.74)) : 0;
    const sideStudy=smooth(lastT,7.10,7.26)*(1-smooth(lastT,7.26,7.40));
    let screenY = lerp(lerp(a.y || 0, b.y || 0, v), -0.18, phonePortrait);
    const phonePerformance=!exploring&&camera.aspect<.8?performanceFraming(lastT):0;
    if(!exploring&&camera.aspect<1.3)screenY=lerp(screenY,camera.aspect<.8?-.07:-.10,performanceFraming(lastT));
    const phoneLanding=!exploring&&(camera.aspect<=1.3||innerWidth<=760)?smooth(lastT,7.43,7.78):0;
    screenY=lerp(screenY,-.10,phoneLanding);
    // Fill the longest viewport dimension with the lens on portrait screens too.
    const portalFrame=!exploring?smooth(lastT,5.70,5.86)*(1-smooth(lastT,6.44,6.64)):0;
    const aspectScale=lerp(
      Math.max(1,(camera.aspect<1.1?1.25:1.6)/camera.aspect),
      Math.max(1,(camera.aspect<.8?1.48:1.6)/Math.max(camera.aspect,1)),portalFrame);
    camera.position
      .copy(target)
      .addScaledVector(
        dir,
        portraitDistance *
          aspectScale *
          lerp(1,.81+.065*sideStudy,phoneFlight) *
          lerp(1, 0.85, phonePortrait) * lerp(1,.8,phonePerformance),
      );
    camera.lookAt(target);
    const rect = mount.getBoundingClientRect();
    let screenX = lerp(a.x, b.x, v);
    screenX=lerp(screenX,0,phoneLanding);
    if (camera.aspect < 1.1)
      screenX *= lerp(0.3, 1, smooth(Math.abs(screenX), 0.3, 0.9));
    screenX-=.045*sideStudy*phoneFlight;
    camera.setViewOffset(
      rect.width,
      rect.height,
      -rect.width * screenX,
      -rect.height * (screenY - 0.08 * phonePortrait),
      rect.width,
      rect.height,
    );
    controls.target.copy(target);
    camera.updateMatrixWorld(true);
  }
  // Annotation targets live on real rendered surfaces, separately from the
  // immutable camera framing anchors (which intentionally sit above some parts).
  const annotationParts = {
    battery: "BAT29_TOP_LID",
    thermal: "TH30_COOLING_FIN.008",
    computer: "FC30_RADIO_MODULE",
    tray: "TR30_POCKETED_TRAY",
  };
  const sourceParts = new Map();
  model.traverse(o => { if(o.userData.name) sourceParts.set(o.userData.name,o); });
  const annotationTargets = new Map();
  function annotationPoint(name) {
    if (!annotationTargets.has(name)) {
      // GLTFLoader sanitizes punctuation in runtime names. Its source-name
      // metadata identifies the authored mesh without relying on that rewrite.
      const part=sourceParts.get(annotationParts[name])||model.getObjectByName(ROOTS[name]);
      part.updateWorldMatrix(true,true);
      const bounds=new THREE.Box3().setFromObject(part),size=bounds.getSize(new THREE.Vector3());
      const origin=bounds.getCenter(new THREE.Vector3());
      origin.x+=size.x*.15;origin.z+=size.z*.12;origin.y=bounds.max.y+.02;
      const ray=new THREE.Raycaster(origin,new THREE.Vector3(0,-1,0));
      const hit=ray.intersectObject(part,true)[0];
      const point=hit?.point||bounds.getCenter(new THREE.Vector3());
      annotationTargets.set(name,{part,local:part.worldToLocal(point.clone()),surfaceHit:!!hit});
    }
    const {part,local}=annotationTargets.get(name);
    return part.localToWorld(local.clone());
  }
  const anatomy = createAnatomy({
    root: document.querySelector("#model-labels"),
    source: document.querySelector(".layer-key"),
    project: name => {
      const p=annotationPoint(name).project(camera);
      return {x:(p.x*.5+.5)*mount.clientWidth,y:(-.5*p.y+.5)*mount.clientHeight,z:p.z,
        surface:annotationTargets.get(name).part.userData.name||annotationTargets.get(name).part.name,surfaceHit:annotationTargets.get(name).surfaceHit};
    },
  });
  const performanceParts=new Map(),performanceTargets=new Map();
  studies.computer.object.traverse(o=>{if(o.userData.name)performanceParts.set(o.userData.name,o);});
  const performanceLabels=createPerformance({
    root:document.querySelector('#performance-labels'),
    source:document.querySelector('.performance-source'),
    project:name=>{
      if(!performanceTargets.has(name)){
        const part=performanceParts.get(PERFORMANCE_PARTS[name]);
        if(!part)throw new Error(`Missing performance surface: ${name}`);
        part.updateWorldMatrix(true,true);
        const bounds=new THREE.Box3().setFromObject(part),origin=bounds.getCenter(new THREE.Vector3());
        origin.y=bounds.max.y+.01;
        const hit=new THREE.Raycaster(origin,new THREE.Vector3(0,-1,0)).intersectObject(part,true)[0];
        const local=part.worldToLocal((hit?.point||bounds.getCenter(new THREE.Vector3())).clone());
        performanceTargets.set(name,{part,local,surfaceHit:!!hit});
      }
      const {part,local,surfaceHit}=performanceTargets.get(name),p=part.localToWorld(local.clone()).project(camera);
      return {x:(p.x*.5+.5)*mount.clientWidth,y:(-.5*p.y+.5)*mount.clientHeight,z:p.z,surface:part.userData.name||part.name,surfaceHit};
    },
  });
  function labels(t) { anatomy.update(t);performanceLabels.update(t); }
  function update(t) {
    if (exploring || t === lastT) return;
    lastT = t;
    lastState = sampleStory(t);
    flightRig.position.set(
      lastState.flight.x,
      lastState.lift + lastState.airframeExit,
      lastState.flight.z,
    );
    flightRig.rotation.set(
      lastState.flight.pitch,
      lastState.flight.yaw,
      lastState.flight.roll,
    );
    pose(lastState.pose);
    updateStudies(lastState.details);
    visibility(lastState.weights, 1, lastState.rotors);
    scene.fog.density = 0;
    const studyLight = smooth(t, 2.9, 3.05) * (1 - smooth(t, 4.52, 4.85));
    storyLight.key = 2.45 - 0.7 * lastState.sky - 1.0 * studyLight;
    storyLight.rim = 2.1 - 0.35 * studyLight;
    storyLight.environment = 0.95 - 0.1 * lastState.sky - 0.27 * studyLight;
    applyIntroLight();
    platform.update(
      lastState.platformAlpha,
      lastState.lift,
      // A portrait viewport sees farther below the airframe. Carry the launch
      // surface beyond that extended view before its visibility boundary.
      lastState.platformDrop +
        0.6 * smooth(t, 0.72, 0.97) * (1 - smooth(camera.aspect, 0.8, 1.1))*(1-smooth(t,7.43,7.74)),
    );
    flightRig.visible = lastState.modelAlpha > 0.01;
    atmosphere.uniforms.uT.value = t;
    atmosphere.updateWorlds(t);
    atmosphere.uniforms.uSky.value = lastState.backgroundSky;
    atmosphere.uniforms.uGlass.value = lastState.glass;
    const shot = lastState.camera;
    setCamera(shot.a, shot.b, shot.v, 0, shot.dir);
    labels(t);
    dirty = true;
  }
  function resize() {
    const rect = mount.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    anatomy.resize(rect.width, rect.height);
    performanceLabels.resize(rect.width, rect.height);
    renderer.setSize(rect.width, rect.height, false);
    background.setSize(innerWidth, innerHeight, false);
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
    for(const {m,target:shellTarget} of shellTargets){
      if(Math.abs(m.color.r-shellTarget.r)+Math.abs(m.color.g-shellTarget.g)+Math.abs(m.color.b-shellTarget.b)>1e-5){
        m.color.lerp(shellTarget,1-Math.exp(-dt/.12));dirty=true;
      }else m.color.copy(shellTarget);
    }
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
        lastState.flight.angularFreedom,
      );
      flightRig.position.set(
        lastState.flight.x + hoverState.x,
        lastState.lift + lastState.airframeExit + hoverState.y,
        lastState.flight.z + hoverState.z,
      );
      flightRig.rotation.set(
        lastState.flight.pitch + hoverState.pitch,
        lastState.flight.yaw + hoverState.yaw,
        lastState.flight.roll + hoverState.roll,
      );
      for (const { spin, disc, sign } of rotors) {
        // Integrate velocity so slowing down settles at the current blade angle.
        spin.rotation.y = (spin.rotation.y + dt * lastState.rotors * 58 * sign) % (Math.PI * 2);
        disc.visible =
          lastState.rotors > 0.01 && lastState.weights.exterior > 0.01;
        disc.material.uniforms.uSpeed.value =
          lastState.rotors * lastState.weights.exterior * lastState.modelAlpha;
        disc.material.uniforms.uTime.value = seconds * sign;
        disc.material.uniforms.uSky.value = lastState.sky;
      }
      atmosphere.uniforms.uTime.value = seconds;
      atmosphere.uniforms.uPointer.value.set(pointerX, pointerY);
      dirty = true;
    }
    if (!dirty) return;
    const start = performance.now();
    renderer.clear();
    if (exploring) {
      renderer.render(atmosphere.scene, atmosphere.camera);
      renderer.clearDepth();
    } else background.render(atmosphere.scene, atmosphere.camera);
    renderer.render(scene, camera);
    timings.push(performance.now() - start);
    if (timings.length > 240) timings.shift();
    lastRender = now;
    frames++;
    dirty = false;
  }
  function applyIntroLight() {
    // A rim finds the silhouette before the broad studio key fills the shell.
    // No opacity, camera, geometry, texture or exposure changes are involved.
    const ambient = smooth(intro, .12, 1);
    rim.intensity = storyLight.rim * smooth(intro, .02, .58);
    key.intensity = storyLight.key * smooth(intro, .16, .96);
    fill.intensity = .35 * smooth(intro, .24, 1);
    hemisphere.intensity = .26 * smooth(intro, .18, 1);
    scene.environmentIntensity = storyLight.environment * ambient;
    atmosphere.uniforms.uBoot.value = smooth(intro, .1, 1);
    for (const [m, base] of introMaterials) {
      if (base.env !== null) m.envMapIntensity = base.env * ambient;
      if (base.emissive !== undefined) m.emissiveIntensity = base.emissive * smooth(intro, .05, .8);
      if (base.basicColor) m.color.copy(base.basicColor).multiplyScalar(ambient);
    }
  }
  function setIntro(value) {
    const next = THREE.MathUtils.clamp(value, 0, 1);
    if (next === intro) return;
    intro = next;
    applyIntroLight();
    dirty = true;
  }
  async function warmIntro() {
    setIntro(0);
    lastT = -1;
    update(0);
    render(performance.now());
    // compileAsync prepares programs, but the first draw also uploads buffers
    // and textures. Wait for that GPU work before starting the visible counter.
    const gl = renderer.getContext();
    const fence = gl.fenceSync(gl.SYNC_GPU_COMMANDS_COMPLETE, 0);
    if (!fence) throw new Error("Unable to prepare the hero frame");
    gl.flush();
    const started = performance.now();
    await new Promise((resolve, reject) => {
      function poll() {
        const result = gl.clientWaitSync(fence, 0, 0);
        if (result === gl.ALREADY_SIGNALED || result === gl.CONDITION_SATISFIED) {
          gl.deleteSync(fence);
          requestAnimationFrame(() => requestAnimationFrame(resolve));
        } else if (result === gl.WAIT_FAILED || gl.isContextLost() || performance.now() - started > 30000) {
          gl.deleteSync(fence);
          reject(new Error("Hero frame preparation did not complete"));
        } else requestAnimationFrame(poll);
      }
      requestAnimationFrame(poll);
    });
  }
  function inspect() {
    const box=new THREE.Box3().setFromObject(model),corners=[];
    for(const x of [box.min.x,box.max.x])for(const y of [box.min.y,box.max.y])for(const z of [box.min.z,box.max.z])corners.push(new THREE.Vector3(x,y,z).project(camera));
    return {
      ready: true,
      projectedModel:{left:Math.min(...corners.map(p=>p.x*.5+.5)),right:Math.max(...corners.map(p=>p.x*.5+.5)),top:Math.min(...corners.map(p=>-.5*p.y+.5)),bottom:Math.max(...corners.map(p=>-.5*p.y+.5))},
      landingFeet: ['FL','FR','RL','RR'].map(side=>{
        const foot=model.getObjectByName(`FOOT_PAD_${side}`);
        return {side,clearance:foot?new THREE.Box3().setFromObject(foot).min.y-platform.group.position.y:null};
      }),
      finish:{id:selectedFinish.id,name:selectedFinish.name,shellMaterials:shellMaterials.map(m=>({name:m.name,color:m.color.getHexString()})),
        textureAndFinishPreserved:finishBaselines.every(({m,roughness,metalness,maps})=>m.roughness===roughness&&m.metalness===metalness&&['map','normalMap','roughnessMap','metalnessMap','aoMap'].every((k,i)=>m[k]===maps[i])),
        otherColorsPreserved:finishBaselines.every(({m,color})=>shellMaterials.includes(m)||!color||m.color.equals(color))},
      version: 4,
      batteryFinishes: [...materialCache.values()]
        .filter((m) => /^V31/.test(m.name))
        .map((m) => ({
          name: m.name,
          color: m.color.toArray(),
          metalness: m.metalness,
          roughness: m.roughness,
          reflectionIntensity: m.envMap ? m.envMapIntensity : scene.environmentIntensity,
          colorMap: m.map?.name || null,
          normalMap: m.normalMap?.name || null,
        })),
      motherboardFinishes: [...materialCache.values()]
        .filter((m) => /^V32/.test(m.name))
        .map((m) => ({
          name: m.name,
          roughness: m.roughness,
          metalness: m.metalness,
          reflectionIntensity: m.envMap ? m.envMapIntensity : scene.environmentIntensity,
          colorMap: m.map?.name || null,
          normalMap: m.normalMap?.name || null,
        })),
      solidMaterialViolations: [...materialCache.values()]
        .filter(
          (m) =>
            !m.userData.baseTransparent &&
            (m.transparent ||
              m.opacity !== m.userData.baseOpacity ||
              !m.depthWrite),
        )
        .map((m) => m.name),
      studies: Object.fromEntries(
        Object.entries(studies).map(([k, s]) => [
          k,
          { visible: s.rig.visible, position: s.rig.position.toArray() },
        ]),
      ),
      intro,
      anatomy: anatomy.inspect(),
      performance: performanceLabels.inspect(),
      flightWorlds: atmosphere.inspect(),
      backgroundSky: atmosphere.uniforms.uSky.value,
      introLighting: {
        key: key.intensity, rim: rim.intensity, fill: fill.intensity,
        hemisphere: hemisphere.intensity, environment: scene.environmentIntensity,
        exposure: renderer.toneMappingExposure,
        platform: platform.group.position.toArray(),
        platformVisible:platform.group.visible,
      },
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
    for (const study of Object.values(studies)) study.rig.visible = false;
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
        state.view.distance * Math.max(0.7, 1.0 / camera.aspect),
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
  background.domElement.addEventListener("webglcontextlost", (e) => {
    e.preventDefault();
    active = false;
    onFailure();
  });
  resize();
  update(0);
  setIntro(initialIntro);
  await renderer.compileAsync(scene, camera);
  return {
    update,
    setFinish,
    setIntro,
    warmIntro,
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
    platformScreenY() {
      const p = platform.group
        .localToWorld(new THREE.Vector3(0, 0, -0.25))
        .project(camera);
      return (1 - p.y) * 0.5 * mount.clientHeight;
    },
    explore,
    close,
    setActive(v) {
      active = v;
      dirty = true;
    },
    verifySequence() {
      const saved = lastT,
        checks = [];
      const check = (name, pass, detail) =>
        checks.push({ name, pass, ...(detail ? { detail } : {}) });
      const samples = [
        0, 0.22, 0.36, 0.65, 1, 1.24, 1.43, 1.72, 1.98, 2.18, 2.35, 2.57, 2.73,
        2.9, 3.02, 3.3, 3.7, 3.91, 4.19, 4.65, 5.16, 5.4, 5.72, 5.88, 6, 6.61,
        7, 8,
      ];
      const snapshots = [];
      let solid = true,
        finite = true;
      for (const t of samples) {
        lastT = -1;
        update(t);
        solid &&= [...materialCache.values()].every(
          (m) =>
            m.transparent === m.userData.baseTransparent &&
            m.opacity === m.userData.baseOpacity &&
            m.depthWrite === m.userData.baseDepthWrite,
        );
        finite &&= [...camera.position.toArray(), ...target.toArray()].every(
          Number.isFinite,
        );
        snapshots.push([...camera.position.toArray(), ...target.toArray()]);
      }
      check(
        "All 28 sampled shots retain original material alpha and depth",
        solid,
      );
      check("All camera positions and targets are finite", finite);
      let reversible = true;
      samples
        .slice()
        .reverse()
        .forEach((t, i) => {
          lastT = -1;
          update(t);
          const values = [...camera.position.toArray(), ...target.toArray()];
          reversible &&= values.every(
            (v, j) => Math.abs(v - snapshots.at(-1 - i)[j]) < 1e-9,
          );
        });
      check("Camera framing reverses exactly across 28 shots", reversible);
      const inFrame = (root) => {
        root.updateWorldMatrix(true, true);
        const frustum = new THREE.Frustum().setFromProjectionMatrix(
          new THREE.Matrix4().multiplyMatrices(
            camera.projectionMatrix,
            camera.matrixWorldInverse,
          ),
        );
        let found = false;
        root.traverseVisible((o) => {
          if (!o.isMesh) return;
          o.geometry.computeBoundingBox();
          if (
            frustum.intersectsBox(
              o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld),
            )
          )
            found = true;
        });
        return found;
      };
      for (const [name, t] of [
        ["battery", 2.84001],
        ["battery", 3.84999],
        ["computer", 3.57001],
        ["computer", 4.79999],
        ["optics", 4.52001],
      ]) {
        lastT = -1;
        update(t);
        check(
          name + " visibility boundary is outside the camera at " + t,
          !inFrame(studies[name].rig),
        );
      }
      for (const t of [3.19999, 6.72001]) {
        lastT = -1;
        update(t);
        check(
          "Airframe visibility boundary is outside the camera at " + t,
          !inFrame(flightRig),
        );
      }
      lastT = -1;
      update(0.96999);
      check(
        "Platform leaves the frame before hiding",
        !inFrame(platform.group),
      );
      lastT = -1;
      update(2.73);
      check(
        "Drone is closed before the component procession",
        lastState.pose.body === 0 &&
          !Object.values(lastState.details).some((d) => d.visible),
      );
      lastT = -1;
      update(5.9);
      check(
        "Lens is fully assembled before the optical entrance",
        lastState.details.optics.progress === 0 && lastState.lensPass > 0.99,
      );
      lastT = -1;
      update(saved);
      dirty = true;
      return {
        passed: checks.filter((c) => c.pass).length,
        total: checks.length,
        checks,
      };
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
      const assembly = ["battery", "computer", "optics", "exploded"].includes(
        name,
      );
      explore(assembly ? name : "flight");
      controls.enabled = false;
      renderer.setPixelRatio(1);
      renderer.setSize(1800, 1350, false);
      camera.aspect = 4 / 3;
      camera.clearViewOffset();
      camera.updateProjectionMatrix();
      const sky = name === "sky";
      const view = assembly ? explorerPose(name).view : null;
      target.copy(
        assembly ? focus(view.focus) : new THREE.Vector3(0, sky ? 0 : -0.02, 0),
      );
      const dir = assembly ? view.dir : sky ? [0.35, 0.24, 1] : [0.27, 0.34, 1];
      const distance = assembly
        ? { battery: 0.48, computer: 0.35, optics: 0.48, exploded: 1.22 }[name]
        : sky
          ? 0.88
          : 0.97;
      camera.position
        .copy(target)
        .addScaledVector(
          new THREE.Vector3().fromArray(dir).normalize(),
          distance,
        );
      camera.lookAt(target);
      platform.update(name === "hero" ? 1 : 0, 0);
      visibility(
        explorerPose(assembly ? name : "flight").weights,
        1,
        sky ? 1 : 0,
      );
      for (const { disc } of rotors) {
        disc.visible = sky;
        disc.material.uniforms.uSpeed.value = 1;
        disc.material.uniforms.uSky.value = sky ? 1 : 0;
      }
      key.intensity = assembly ? 1.45 : sky ? 1.8 : 2.45;
      scene.environmentIntensity = assembly ? 0.68 : 0.95;
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
      transmissionBackdrop.material.dispose();
      atmosphere.dispose();
      platform.dispose();
      controls.dispose();
      background.dispose();
      background.domElement.remove();
      renderer.dispose();
      renderer.domElement.remove();
      scene.environment.dispose();
    },
  };
}
