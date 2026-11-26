import * as THREE from "three";
import { PLATFORM_TOP, ROTOR_RADIUS } from "./anchors.js";
export function createAtmosphere() {
  const uniforms = {
    uTime: { value: 0 },
    uT: { value: 0 },
    uSky: { value: 0 },
    uGlass: { value: 0 },
    uAspect: { value: 1.6 },
    uBoot: { value: 1 },
    uExplore: { value: 0 },
    uPointer: { value: new THREE.Vector2() },
  };
  const material = new THREE.ShaderMaterial({
    depthWrite: false,
    depthTest: false,
    toneMapped: false,
    uniforms,
    vertexShader:
      "varying vec2 vUv; void main(){vUv=uv;gl_Position=vec4(position.xy,0.,1.);}",
    fragmentShader: `precision highp float; varying vec2 vUv;
 uniform float uTime,uT,uSky,uGlass,uAspect,uBoot,uExplore; uniform vec2 uPointer;
 float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453123);}
 float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);}
 float fbm(vec2 p){float v=0.,a=.5;for(int i=0;i<4;i++){v+=a*noise(p);p=p*2.03+vec2(17.1,9.2);a*=.5;}return v;}
 void main(){
 vec2 uv=vUv;vec2 c=(uv-.5)*vec2(uAspect,1.);float r=length(c);
 uv+=(uv-.5)*pow(r,3.)*.045*uGlass+uPointer*.006*uGlass;
 float horizon=.29+.026*sin(uT*.48);float y=uv.y-horizon;
 vec3 dark=mix(vec3(.035,.049,.048),vec3(.099,.132,.124),exp(-dot(c*vec2(.65,1.2),c*vec2(.65,1.2))*2.));
 dark+=vec3(.025,.035,.023)*exp(-pow((uv.y-.38+uT*.025)*3.,2.));
 vec3 upper=mix(vec3(.69,.75,.69),vec3(.23,.40,.45),smoothstep(0.,.85,y));
 vec3 lower=mix(vec3(.78,.80,.69),vec3(.94,.85,.66),exp(-abs(y)*13.));
 vec3 sky=mix(lower,upper,smoothstep(-.05,.12,y));
 float n=fbm(vec2(uv.x*4.+uTime*.005,uv.y*12.+uT*.20));
 float veil=smoothstep(.39,.74,n)*exp(-pow((y+.05)*3.6,2.));
 sky=mix(sky,vec3(.94,.93,.82),veil*.6);
 float highCloud=fbm(vec2(uv.x*5.-uTime*.008,uv.y*22.+uT*.18));
 sky+=vec3(.11,.105,.085)*smoothstep(.51,.73,highCloud)*smoothstep(.07,.6,y)*.75;
 vec3 col=mix(dark,sky,uSky);
 float bloom=exp(-length((uv-vec2(.77,.38))*vec2(2.4,5.))*4.);
 col+=mix(vec3(.018,.015,.011),vec3(.12,.075,.03),uSky)*bloom;
 float edge=smoothstep(.46,.9,r);col=mix(col,col*vec3(.83,.95,.96),edge*uGlass*.45);
 col+=vec3(.10,.12,.085)*pow(edge,8.)*uGlass*.28;
 col*=1.-.07*pow(length(c*.78),2.);
 col+= (hash(gl_FragCoord.xy)-.5)/360.;
 col=mix(col,vec3(.075,.105,.095),uExplore);
 col*=mix(.10,1.,uBoot);
 gl_FragColor=vec4(col,1.);
 }`,
  });
  const scene = new THREE.Scene();
  scene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), material));
  return {
    scene,
    camera: new THREE.Camera(),
    uniforms,
    dispose() {
      material.dispose();
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
    color: 0x202c28,
    metalness: 0.92,
    roughness: 0.24,
    roughnessMap: texture,
    clearcoat: 0.25,
    clearcoatRoughness: 0.22,
  });
  const side = new THREE.MeshPhysicalMaterial({
    color: 0x111c18,
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
  const top = new THREE.Mesh(new THREE.CircleGeometry(0.32, 256), metal);
  top.rotation.x = -Math.PI / 2;
  top.position.y = 0.00005;
  group.add(top);
  const copper = new THREE.MeshStandardMaterial({
    color: 0x957157,
    metalness: 0.78,
    roughness: 0.2,
    emissive: 0x916a43,
    emissiveIntensity: 0.12,
  });
  for (const [r, t, y, mat] of [
    [0.3237, 0.00038, -0.0025, copper],
    [0.302, 0.00016, 0.0007, side],
    [0.285, 0.0001, 0.0007, side],
    [0.15, 0.0001, 0.0007, side],
  ]) {
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
  const materials = [metal, side, copper];
  return {
    group,
    update(alpha, lift) {
      group.visible = alpha > 0.01;
      for (const m of materials) {
        const tr = alpha < 0.999;
        if (m.transparent !== tr) {
          m.transparent = tr;
          m.needsUpdate = true;
        }
        m.opacity = alpha;
        m.depthWrite = !tr;
      }
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
    uniforms: { uSpeed: { value: 0 }, uTime: { value: 0 } },
    vertexShader:
      "varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}",
    fragmentShader: `varying vec2 vUv;uniform float uSpeed,uTime;void main(){vec2 p=vUv*2.-1.;float r=length(p);float angle=atan(p.y,p.x);float body=smoothstep(.16,.34,r)*(1.-smoothstep(.84,1.,r));float tip=exp(-pow((r-.93)*55.,2.));float bands=.98+.02*sin(r*82.);float arc=.86+.14*sin(angle*2.-uTime*28.);float alpha=(body*.105*bands*arc+tip*.04)*uSpeed;gl_FragColor=vec4(.66,.71,.65,alpha);}`,
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
