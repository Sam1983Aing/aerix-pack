# AERIX — V3 / Ascent

Preview: **http://127.0.0.1:8765/site/?v=3**

V3 expands the departure into a full cinematic orbit, holds and recloses the exploded architecture, and presents the individual components in a slower vertical procession. Solid product geometry occludes the text. The optical assembly closes before the camera enters the glass view, and the drone returns in a front three-quarter sky shot.

## Run

Vanilla HTML, CSS and JavaScript; no build step or runtime CDN. From the project root:

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

Reuse the existing server when port 8765 is occupied. Serve over HTTP for ES modules and the GLB. The `site/` folder can be copied to a static host. The preserved first iteration is at `/site-v1/`; the modeling viewer remains at `/viewer/?v=30`.

## Controls

Scroll forward or backward through the same reversible sequence. Header links navigate chapters. The side scale indicates story progress rather than physical altitude. The introduction is skippable and runs once per tab. Motion off displays native images and readable document sections. Mobile and reduced-motion visitors start in that static view.

**Explore the object** opens eight manual poses: Flight, Architecture, Battery, Thermal, Computer, Tray, Optics and Folded. Drag to orbit; wheel/pinch to zoom. A focused canvas supports arrows and +/−. Escape restores the story position and opener focus.

## Source quality and component refinement

`assets/aerix-quality-v02.glb` retains the original 2,613,305 active triangles, 48 encoded texture maps, seven clips and 45 animated pivots. It is 94,509,268 bytes. No simplification, quantization, texture resizing or lossy texture encoding is applied. The master Blender files and review exports remain in the project.

`js/anchors.js` defines the stable model offset, semantic roots and camera targets. Preserve those names, transforms and pivots when refining an individual part. Camera framing does not derive from mesh bounds. V3 component studies share geometry and materials from that same asset; a component refinement therefore reaches both the complete drone and its presentation automatically. Changed proportions still warrant a framing review.

## Art direction

| File | Responsibility |
| --- | --- |
| `js/story.js` | Camera keys, chapter lengths, assembly timing and component travel |
| `js/flight.js` | Reversible banking and bounded ambient hover |
| `js/scene.js` | Source asset, two-canvas compositing, refraction, studies and explorer |
| `js/effects.js` | Platform engraving, atmosphere and rotor blur |
| `styles.css` | One-font section headlines, reverse-moving copy and responsive layout |
| `main.js` | One GSAP clock, Lenis, navigation and review controls |
| `index.html` | Semantic content and native fallback posters |

Solid materials never fade during shot changes. Outgoing objects move beyond the camera before hiding. Atmosphere is behind the HTML and opaque geometry above it. The hero title fades based on its projected meeting with the platform. Inspection intervals exclude ambient hover.

The renderer pauses while static or hidden. Foreground pixel ratio is capped at 2 on desktop and 1.5 in the phone explorer. Hero and sky fallback posters are native 1800 × 1350 captures, encoded losslessly. Interior fallback images remain native Blender renders.

## Review

```sh
node scripts/web/verify-v3-story.mjs
```

Open `/site/?v=3&qa` for precise story seeking, render diagnostics and the 13-check browser audit. **Hero poster** and **Sky poster** download native transparent PNGs. Review controls do not appear at the normal URL. `/renders/site-v03/responsive.html` provides phone, tablet and laptop iframe viewports.

The current change and validation record is `../docs/CINEMATIC-REFINEMENT-V3.md`. Automated math/asset results are in `../renders/site-v03/story-verification.json`; browser results in `../renders/site-v03/browser-verification.json`. Earlier V2 suites and reviews document the former timeline. Before-state files for this revision are in `../renders/site-v03/before/`.

Deployment and physical-device browser profiling are separate rollout work. The ending uses the live model. Third-party notices are in `THIRD-PARTY.md`.
