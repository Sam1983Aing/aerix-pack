import * as THREE from "three";
import { PLATFORM_TOP, ROTOR_RADIUS } from "./anchors.js";
import { POV_WORLD, FLIGHT_WORLDS, flightWorldsAt, landscapeEntryAt, CLIP_STARTS, CLIP_ENDS } from "./flight-worlds.js?v=11";
import { WORLD_PREVIEWS } from "./world-previews.js?v=7";
const WORLD_THRESHOLDS=[5,6,6.65,6.88,7];
// Round 2: one backdrop per finish, in display space. deep = the edges, lift = the glow
// behind the drone, glow = the soft horizontal band, bloom = the light spot on the right.
// Titanium Blue is the original ThreeUI blue.
export const BACKDROPS = {
  "titanium-blue":    { deep: [.024,.050,.092], lift: [.066,.124,.202], glow: [.016,.033,.060], bloom: [.010,.030,.064] },
  "obsidian-metal":   { deep: [.026,.029,.034], lift: [.082,.090,.102], glow: [.019,.021,.025], bloom: [.016,.018,.022] },
  "tactical-green":   { deep: [.026,.036,.024], lift: [.080,.104,.068], glow: [.018,.027,.016], bloom: [.012,.024,.012] },
  "crimson-alloy":    { deep: [.060,.018,.020], lift: [.160,.046,.046], glow: [.040,.012,.012], bloom: [.036,.010,.010] },
  "glacial-titanium": { deep: [.050,.056,.064], lift: [.145,.156,.170], glow: [.030,.034,.040], bloom: [.020,.024,.030] },
};
export function createAtmosphere(assets) {
  // ThreeUI polish: each world starts as a tiny inline preview and the full image streams in
  // through the shared asset queue once the scroll gets close to it (see updateWorlds).
  const loader=new THREE.TextureLoader();
  const worlds=[POV_WORLD,...FLIGHT_WORLDS];
  const loadStates=worlds.map(()=> 'preview');
  let disposed=false, backdropRun=0;
  const vistas=worlds.map((world,i)=>{
    const texture=loader.load(WORLD_PREVIEWS[i]);
    texture.colorSpace=THREE.NoColorSpace;
    texture.minFilter=THREE.LinearMipmapLinearFilter;
    texture.magFilter=THREE.LinearFilter;
    return texture;
  });
  async function loadWorld(index,signal){
    const response=await fetch(new URL(`../assets/${worlds[index].local}`,import.meta.url),{signal});
    if(!response.ok)throw new Error('Environment: HTTP '+response.status);
    // Decode off the main thread. ImageBitmaps ignore texture.flipY, so flip while decoding.
    const bitmap=await createImageBitmap(await response.blob(),{premultiplyAlpha:'none',colorSpaceConversion:'none',imageOrientation:'flipY'});
    if(disposed){bitmap.close();return;}
    vistas[index].dispose();
    vistas[index].image=bitmap;
    vistas[index].needsUpdate=true;
    loadStates[index]='ready';
    if(index===0)document.body.classList.add('aerix-worlds');
  }
  // Round 2: each world also has a video clip. It streams in early, plays once from the moment
  // its world starts to appear (CLIP_STARTS) and rests on its last frame. The page holds the
  // scroll until it ends, so only one clip plays at a time. Scrolling back above its start
  // rewinds it to frame 0, which is the still, so the next pass is seamless.
  const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const clips = worlds.map(() => null);
  let playing = -1;
  async function loadClip(index, signal) {
    const video = document.createElement("video");
    video.muted = true;
    video.playsInline = true;
    video.preload = "auto";
    video.setAttribute("muted", "");
    video.setAttribute("playsinline", "");
    video.src = new URL(`../assets/${worlds[index].clip}`, import.meta.url).href;
    await new Promise((resolve, reject) => {
      video.addEventListener("loadeddata", resolve, { once: true });
      video.addEventListener("error", () => reject(new Error("Clip: " + worlds[index].clip)), { once: true });
      signal?.addEventListener("abort", () => { video.removeAttribute("src"); video.load(); reject(new Error("aborted")); }, { once: true });
    });
    if (disposed) return;
    const texture = new THREE.VideoTexture(video);
    texture.colorSpace = THREE.NoColorSpace;
    texture.minFilter = THREE.LinearFilter;
    texture.magFilter = THREE.LinearFilter;
    texture.generateMipmaps = false;
    clips[index] = { video, texture };
  }
  const textureFor = (index) => clips[index]?.texture || vistas[index];
  function steerClips(t) {
    playing = -1;
    clips.forEach((clip, index) => {
      if (!clip) return;
      const video = clip.video;
      if (CLIP_STARTS[index] == null) return;
      if (t < CLIP_STARTS[index]) {
        // Before its world: parked on frame 0, ready to start without a jump.
        if (!video.paused) video.pause();
        if (video.currentTime > 0 && !video.seeking) video.currentTime = 0;
      } else if (t < CLIP_ENDS[index]) {
        if (video.paused && !video.ended) video.play().catch(() => {});
      } else if (!video.paused) video.pause();
      if (!video.paused) playing = index;
    });
  }
  const vista=vistas[0];
  // Shader colours are authored in display space; the transmission pass converts them to linear.
  vista.colorSpace = THREE.NoColorSpace;
  vista.minFilter = THREE.LinearMipmapLinearFilter;
  vista.magFilter = THREE.LinearFilter;

  const uniforms = {
    uVista: { value: vista },
    uWorld2: { value: vista },
    uWorld3: { value: vista },
    uWorld4: { value: vista },
    uWorld5: { value: vista },
    uWorldMix: {value:new THREE.Vector4()},
    uTime: { value: 0 },
    uT: { value: 0 },
    uSky: { value: 0 },
    uGlass: { value: 0 },
    uAspect: { value: 1.6 },
    uBoot: { value: 1 },
    uExplore: { value: 0 },
    uPointer: { value: new THREE.Vector2() },
    // Round 2: the dark studio takes the tone of the chosen finish (see BACKDROPS).
    uDeep: { value: new THREE.Vector3(...BACKDROPS["titanium-blue"].deep) },
    uLift: { value: new THREE.Vector3(...BACKDROPS["titanium-blue"].lift) },
    uGlow: { value: new THREE.Vector3(...BACKDROPS["titanium-blue"].glow) },
    uBloom: { value: new THREE.Vector3(...BACKDROPS["titanium-blue"].bloom) },
  };
  const material = new THREE.ShaderMaterial({
    depthWrite: false,
    depthTest: false,
    toneMapped: false,
    uniforms,
    vertexShader:
      "varying vec2 vUv; void main(){vUv=uv;gl_Position=vec4(position.xy,0.,1.);}",
    fragmentShader: `precision highp float; varying vec2 vUv;
 uniform float uTime,uT,uSky,uGlass,uAspect,uBoot,uExplore; uniform vec2 uPointer; uniform sampler2D uVista,uWorld2,uWorld3,uWorld4,uWorld5; uniform vec4 uWorldMix; uniform vec3 uDeep,uLift,uGlow,uBloom;
 float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453123);}
 float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);}
 float fbm(vec2 p){float v=0.,a=.5;for(int i=0;i<4;i++){v+=a*noise(p);p=p*2.03+vec2(17.1,9.2);a*=.5;}return v;}
 vec2 travelUV(vec2 uv,vec2 cover,float start,float end,vec2 drift){
   float p=smoothstep(start,end,uT);
   return clamp((uv-.5)*cover/mix(1.04,1.12,p)+.5+drift*p+uPointer*.002,vec2(.001),vec2(.999));
 }
 float cloudDissolve(float p,float cloud){
   // The cloud only feathers the middle of a dissolve. Exact endpoints prevent
   // residual double horizons and make forward/backward scrolling identical.
   return clamp(p+(cloud-.5)*.28*sin(p*3.14159265),0.,1.);
 }
 void main(){
 vec2 uv=vUv;vec2 c=(uv-.5)*vec2(uAspect,1.);float r=length(c);
 uv+=(uv-.5)*pow(r,3.)*.045*uGlass+uPointer*.006*uGlass;
 float horizon=.29+.026*sin(uT*.48);float y=uv.y-horizon;
 vec3 dark=mix(uDeep,uLift,exp(-dot(c*vec2(.65,1.2),c*vec2(.65,1.2))*2.));
 dark+=uGlow*exp(-pow((uv.y-.38+uT*.025)*3.,2.));
 // Slow forward travel with bounded foreground-biased parallax.
 vec2 cover=vec2(min(1.,uAspect/(16./9.)),min(1.,(16./9.)/uAspect));
 // Keep the city registered with the lens overlay until the rim has cleared.
 float forward=smoothstep(6.46,7.5,uT);
 vec2 cityCover=vec2(min(1.,uAspect/(1672./941.)),min(1.,(1672./941.)/uAspect));
 vec2 vistaUV=(uv-.5)*cityCover/mix(1.06,1.18,forward)+.5;
 // Pointer drift must not displace the WebGL city beneath its CSS counterpart.
 vistaUV.x+=(.018+uPointer.x*.003)*forward;
 vistaUV.y-=.014*forward;
 vec3 sky=texture2D(uVista,clamp(vistaUV,vec2(.001),vec2(.999))).rgb;
 float cloud=fbm(uv*vec2(3.6,2.4)+vec2(uT*.3,0.));
 vec4 blends=vec4(cloudDissolve(uWorldMix.x,cloud),cloudDissolve(uWorldMix.y,cloud),cloudDissolve(uWorldMix.z,cloud),cloudDissolve(uWorldMix.w,cloud));
 sky=mix(sky,texture2D(uWorld2,travelUV(uv,cover,6.48,7.12,vec2(-.016,-.012))).rgb,blends.x);
 sky=mix(sky,texture2D(uWorld3,travelUV(uv,cover,7.07,7.23,vec2(.012,-.008))).rgb,blends.y);
 sky=mix(sky,texture2D(uWorld4,travelUV(uv,cover,7.18,7.34,vec2(-.01,-.01))).rgb,blends.z);
 sky=mix(sky,texture2D(uWorld5,travelUV(uv,cover,7.29,7.55,vec2(.008,-.006))).rgb,blends.w);
 // Sparse drifting mist gives the near plane a different speed from the vista.
 float mist=fbm(vec2(uv.x*3.-uTime*.008,uv.y*9.+forward*.8));
 float veil=smoothstep(.57,.80,mist)*pow(1.-uv.y,2.)*.15;
 sky=mix(sky,vec3(.65,.78,.90),veil);
 sky*=mix(.84,1.,smoothstep(.0,.75,uv.y));
 vec3 col=mix(dark,sky,uSky);
 float bloom=exp(-length((uv-vec2(.77,.38))*vec2(2.4,5.))*4.);
 col+=mix(uBloom,vec3(.015,.026,.040),uSky)*bloom;
 float edge=smoothstep(.46,.9,r);col=mix(col,col*vec3(.83,.95,.96),edge*uGlass*.62);
 col+=vec3(.10,.12,.085)*pow(edge,8.)*uGlass*.34;
 col*=1.-.26*pow(length(c*.78),2.);
 col+= (hash(gl_FragCoord.xy)-.5)/360.;
 col=mix(col,vec3(.036,.066,.112),uExplore);
 // Match the dark preparation screen exactly, then illuminate the same atmosphere.
 col=mix(vec3(3.,5.,8.)/255.,col,uBoot);
 gl_FragColor=vec4(col,1.);
 }`,
  });
  const scene = new THREE.Scene();
  scene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), material));
  return {
    scene,
    camera: new THREE.Camera(),
    uniforms,
    // True while a clip is playing, so the render loop keeps drawing new video frames.
    isPlaying(){ return clips.some(clip=>clip&&!clip.video.paused); },
    // For the clip hold in main.js: has this world's clip loaded, and has it finished?
    clipStatus(index){ const clip=clips[index]; if(!clip)return {ready:false,ended:false,time:0,duration:0}; const v=clip.video; return {ready:true,ended:v.ended,time:v.currentTime,duration:v.duration||0,paused:v.paused}; },
    // Ease the studio backdrop towards a finish over about a second. onFrame keeps rendering.
    setBackdrop(id, onFrame = () => {}) {
      const target = BACKDROPS[id] || BACKDROPS["titanium-blue"];
      const keys = { uDeep: "deep", uLift: "lift", uGlow: "glow", uBloom: "bloom" };
      const from = Object.fromEntries(Object.keys(keys).map((u) => [u, uniforms[u].value.clone()]));
      const started = performance.now(), duration = 1100, run = ++backdropRun;
      const step = (now) => {
        if (run !== backdropRun) return;
        const t = Math.min(1, (now - started) / duration), e = t * t * (3 - 2 * t);
        for (const [u, k] of Object.entries(keys)) uniforms[u].value.copy(from[u]).lerp(new THREE.Vector3(...target[k]), e);
        onFrame();
        if (t < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    },
    updateWorlds(t) {
      // Request each world as the scroll reaches its threshold. The world on screen jumps the queue.
      const active=t<6.48?0:flightWorldsAt(t).active+1;
      WORLD_THRESHOLDS.forEach((threshold,index)=>{
        if(t>=threshold)assets.request('world:'+index,signal=>loadWorld(index,signal),index===active?-10:5+Math.abs(index-active),true).catch(()=>{});
        // Clips load early so each one can start the moment its world appears: the four
        // landscapes load while the lens opens. The city has no clip.
        if(worlds[index].clip&&t>=5.6&&!reducedMotion)assets.request('clip:'+index,signal=>loadClip(index,signal),t>=5.3&&index===active?-9:6+index,true).catch(()=>{});
      });
      uniforms.uVista.value=textureFor(0);
      const names=['uWorld2','uWorld3','uWorld4','uWorld5'];
      names.forEach((name,i)=>{ uniforms[name].value=textureFor(i+1); });
      steerClips(t);
      uniforms.uWorldMix.value.fromArray([landscapeEntryAt(t),...flightWorldsAt(t).mixes]);
    },
    inspect(){const t=uniforms.uT.value,entry=landscapeEntryAt(t),flight=flightWorldsAt(t);return {clips:clips.map(c=>c&&{time:+c.video.currentTime.toFixed(2),paused:c.video.paused,ended:c.video.ended}),playing,worlds:worlds.map((w,i)=>({name:w.name,state:loadStates[i],width:vistas[i].image?.width,height:vistas[i].image?.height})),...flight,sceneWeights:[1-entry,...flight.weights.map(w=>w*entry)]};},
    dispose() {
      disposed=true;
      clips.forEach(clip=>{ if(!clip)return; clip.video.pause(); clip.video.removeAttribute('src'); clip.video.load(); clip.texture.dispose(); });
      material.dispose();
      vistas.forEach(texture=>{texture.image?.close?.();texture.dispose();});
      scene.children[0].geometry.dispose();
    },
  };
}
export function createPlatform() {
  const group = new THREE.Group();
  group.name = "V2_LAUNCH_PLATFORM";
  group.position.y = PLATFORM_TOP;
  // The machining lives in roughness, leaving a clean dark metallic color.
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = 1024;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#d8d8d8";
  ctx.fillRect(0, 0, 1024, 1024);
  let seed = 217;
  const random = () => {
    seed = (seed * 16807) % 2147483647;
    return (seed - 1) / 2147483646;
  };
  for (let i = 0; i < 1700; i++) {
    ctx.beginPath();
    ctx.arc(512, 512, random() * 724, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(170,170,170,${0.015 + random() * 0.025})`;
    ctx.lineWidth = 0.35 + random() * 0.35;
    ctx.stroke();
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.anisotropy = 8;
  const metal = new THREE.MeshPhysicalMaterial({
    color: 0x202c3e,
    metalness: 0.92,
    roughness: 0.24,
    roughnessMap: texture,
    clearcoat: 0.25,
    clearcoatRoughness: 0.22,
  });
  const side = new THREE.MeshPhysicalMaterial({
    color: 0x101927,
    metalness: 0.9,
    roughness: 0.2,
    clearcoat: 0.6,
    clearcoatRoughness: 0.16,
  });
  // Continuous rounded metal shoulder; no overlapping coplanar cylinder caps.
  const profile = new THREE.Path();
  profile.moveTo(0.304, -0.026);
  profile.lineTo(0.318, -0.026);
  profile.quadraticCurveTo(0.324, -0.026, 0.324, -0.02);
  profile.lineTo(0.324, -0.004);
  profile.quadraticCurveTo(0.324, 0, 0.32, 0);
  group.add(
    new THREE.Mesh(new THREE.LatheGeometry(profile.getPoints(48), 256), side),
  );
  metal.onBeforeCompile = (shader) => {
    shader.vertexShader = shader.vertexShader
      .replace(
        "#include <common>",
        "#include <common>\nvarying vec2 vMachining;",
      )
      .replace(
        "#include <begin_vertex>",
        "#include <begin_vertex>\nvMachining=position.xy;",
      );
    shader.fragmentShader = shader.fragmentShader
      .replace(
        "#include <common>",
        "#include <common>\nvarying vec2 vMachining;",
      )
      .replace(
        "#include <color_fragment>",
        `#include <color_fragment>
      float radius=length(vMachining);
      float edge=min(abs(radius-.302),min(abs(radius-.285),abs(radius-.15)));
      float aa=max(fwidth(radius),.00005);
      float engraving=1.-smoothstep(.00012,.00012+aa,edge);
      diffuseColor.rgb*=1.-.16*engraving;
    `,
      );
  };
  metal.customProgramCacheKey = () => "V3_analytic_machining";
  const top = new THREE.Mesh(new THREE.CircleGeometry(0.32, 256), metal);
  top.rotation.x = -Math.PI / 2;
  top.position.y = 0.00005;
  group.add(top);
  const copper = new THREE.MeshStandardMaterial({
    color: 0x8eaac2,
    metalness: 0.78,
    roughness: 0.2,
    emissive: 0x5b84ab,
    emissiveIntensity: 0.12,
  });
  for (const [r, t, y, mat] of [[0.3237, 0.00038, -0.0025, copper]]) {
    const ring = new THREE.Mesh(new THREE.TorusGeometry(r, t, 12, 256), mat);
    ring.rotation.x = Math.PI / 2;
    ring.position.y = y;
    group.add(ring);
  }
  for (let i = 0; i < 60; i++) {
    const major = i % 5 === 0;
    const tick = new THREE.Mesh(
      new THREE.BoxGeometry(0.00055, 0.0001, major ? 0.006 : 0.0025),
      copper,
    );
    const a = (i / 60) * Math.PI * 2;
    tick.position.set(Math.sin(a) * 0.313, 0.0009, Math.cos(a) * 0.313);
    tick.rotation.y = a;
    group.add(tick);
  }
  // Round 2: light along the platform's top edge, like studio strips caught in a machined lip.
  // A thin core line plus a wider soft halo, brightest on the two front shoulders.
  const edgeMaterial = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
    uniforms: { uAlpha: { value: 1 }, uSoft: { value: 0 }, uScale: { value: 1 } },
    vertexShader:
      "varying vec3 vLocal;varying vec2 vUv;void main(){vLocal=position;vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}",
    fragmentShader: `varying vec3 vLocal;varying vec2 vUv;uniform float uAlpha,uSoft,uScale;
      void main(){
        float a=atan(vLocal.y,vLocal.x);
        float left=pow(max(0.,cos(a-2.25)),6.),right=pow(max(0.,cos(a-.85)),8.),front=pow(max(0.,cos(a-1.5708)),2.);
        float back=pow(max(0.,cos(a+1.5708)),4.);
        float i=(.24+1.9*left+1.5*right+.5*front+.25*back)*uScale;
        float tube=uSoft>.5?pow(1.-abs(vUv.y*2.-1.),2.)*.42:1.;
        vec3 ink=mix(vec3(.62,.80,1.),vec3(.96,.98,1.),clamp(left+right,0.,1.));
        gl_FragColor=vec4(ink*i,1.)*vec4(vec3(tube*uAlpha),tube*uAlpha);
      }`,
  });
  const softEdgeMaterial = edgeMaterial.clone();
  softEdgeMaterial.uniforms.uSoft.value = 1;
  const lowerEdgeMaterial = edgeMaterial.clone();
  lowerEdgeMaterial.uniforms.uScale.value = 0.38;
  // Top lip: a sharp core and a soft halo. Bottom lip: a fainter line so the rim reads as a lit slab.
  for (const [tube, mat, y] of [[0.0009, edgeMaterial, -0.0012], [0.0055, softEdgeMaterial, -0.0012], [0.0007, lowerEdgeMaterial, -0.0258]]) {
    const edge = new THREE.Mesh(new THREE.TorusGeometry(0.3222, tube, 12, 512), mat);
    edge.rotation.x = Math.PI / 2;
    edge.position.y = y;
    edge.renderOrder = 4;
    group.add(edge);
  }
  const shadowMaterial = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    uniforms: { uOpacity: { value: 0.6 }, uSpread: { value: 1 } },
    vertexShader:
      "varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}",
    fragmentShader:
      "varying vec2 vUv;uniform float uOpacity,uSpread;void main(){vec2 p=(vUv-.5)*vec2(1.1,.9)/uSpread;float a=exp(-dot(p,p)*28.)*uOpacity;gl_FragColor=vec4(.015,.022,.020,a);}",
  });
  const shadow = new THREE.Mesh(
    new THREE.PlaneGeometry(0.58, 0.5),
    shadowMaterial,
  );
  shadow.rotation.x = -Math.PI / 2;
  shadow.position.set(0, 0.0011, 0);
  group.add(shadow);
  const materials = [metal, side, copper, edgeMaterial, softEdgeMaterial, lowerEdgeMaterial];
  return {
    group,
    update(alpha, lift, drop = 0) {
      group.visible = alpha > 0.5;
      group.position.y = PLATFORM_TOP - drop;
      edgeMaterial.uniforms.uAlpha.value = softEdgeMaterial.uniforms.uAlpha.value = lowerEdgeMaterial.uniforms.uAlpha.value = alpha;
      shadowMaterial.uniforms.uOpacity.value =
        0.66 * alpha * Math.exp(-lift * 12);
      shadowMaterial.uniforms.uSpread.value = 1 + lift * 2;
    },
    dispose() {
      texture.dispose();
      group.traverse((o) => {
        if (o.isMesh) o.geometry.dispose();
      });
      for (const m of [...materials, shadowMaterial]) m.dispose();
    },
  };
}
export function createRotorDisc() {
  const material = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
    toneMapped: false,
    uniforms: { uSpeed: { value: 0 }, uTime: { value: 0 }, uSky: { value: 0 } },
    vertexShader:
      "varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}",
    fragmentShader: `varying vec2 vUv;uniform float uSpeed,uTime,uSky;void main(){vec2 p=vUv*2.-1.;float r=length(p);float angle=atan(p.y,p.x);float body=smoothstep(.16,.34,r)*(1.-smoothstep(.84,1.,r));float tip=exp(-pow((r-.93)*55.,2.));float bands=.98+.02*sin(r*82.);float arc=.86+.14*sin(angle*2.-uTime*28.);float alpha=(body*mix(.105,.19,uSky)*bands*arc+tip*.04)*uSpeed;vec3 ink=mix(vec3(.66,.75,.87),vec3(.08,.13,.21),uSky);gl_FragColor=vec4(ink,alpha);}`,
  });
  const mesh = new THREE.Mesh(
    new THREE.PlaneGeometry(ROTOR_RADIUS * 2, ROTOR_RADIUS * 2),
    material,
  );
  mesh.rotation.x = -Math.PI / 2;
  mesh.position.y = 0.001;
  mesh.name = "V2_ROTOR_EXPOSURE";
  mesh.renderOrder = 3;
  return mesh;
}
