# AERIX — V4 / Ascent

Preview: http://127.0.0.1:8765/site/?v=4.17.1

The local server already serves this directory. To start it from the project root:

```sh
python3 -m http.server 8765
```

No build step. Local Three.js, GSAP and Lenis dependencies. One GSAP ticker drives
weighted scrolling, flight stabilization and rendering. Desktop and phone use the cinematic
sequence. OS reduced motion and render failures retain readable source-quality posters;
the object explorer remains available. There is no selectable static mode or stored motion preference.

Read `../docs/CINEMATIC-REFINEMENT-V4.md` for changes, evidence and the preservation contract.
Run `node scripts/web/verify-v4-story.mjs` from the project root for deterministic/fidelity checks.
`?v=4.17&qa` adds local review controls. They are absent from the normal preview.
Refresh replays the loader and restarts at the hero,
including when refreshed from a chapter. Fresh chapter links still open directly.
The QA controls include **Replay intro**, **Intro time / Preview intro**, **Replay title**,
and **Title time / Preview title** for reviewing the opening without a refresh.

V4.7 connects the minimal loader directly to the hero through real lighting.
The first 3D frame completes before the 00–100 count starts. A bounded clock
prevents a slow frame from skipping the ending. At 100, the stationary drone and
platform emerge under rim, key and ambient light; the header and title follow.
There is no full-scene crossfade. Read `../docs/LOADER-ILLUMINATION-V4.7.md` for
readiness, timing, verification and the preserved V4.6 baseline.

V4.8 guides the exploded anatomy shot through battery, thermal, flight computer
and structure. Each leader draws from the actual component surface before its
name and product argument appear. Desktop annotations accumulate; compact
screens present one glass panel at a time. Extra scroll distance belongs only
to the open reading hold. The existing model, cameras and later sequence remain
unchanged. See `../docs/ANATOMY-CALLOUTS-V4.8.md` for timing and verification.

V4.9 adds a second motherboard card: “Every detail. Connected.” It explains
copper pathways, shielded modules and fitted connections after the original
overview. The cards share one position and never overlap during their handoff.
Only the open motherboard reading hold gains scroll distance. See
`../docs/CONTROL-DETAIL-V4.9.md` for refinement controls and verification.

V4.9.2 centers the perspective chapter's eyebrow, headline and subtitle as one
group. Brackets and the horizon/crosshair gain contrast, with the horizon below
the text to avoid crossing it. Entrance, disappearance and scroll timing are
unchanged. Refine this in the final V4.9.2 CSS block; browser review and before
source are in `../renders/site-v04-pov-center/`.

V4.2 adds a 3.18-second 3D title drum after the optical loader: READY FOR? → TAKE OFF
→ ASCENT. Scrolling begins after it settles. Skip reveal or a navigation action finishes
the title immediately; reduced-motion and failure paths show ASCENT directly.
The title sequence is in `js/hero-title.js`; its styling is in the V4.2 CSS block.

V4.4 refines the flight computer: circuit artwork on both faces, soldermask and
laminate edge texture, matte chip packages, satin shields, molded connectors,
insulated wiring, plated contacts and finer markings. The live model is
`assets/aerix-flightcore-finish-v32.glb` (137.6 MB), derived from the preserved
battery V31 asset. Original geometry, UVs, normals, pivots, animations and all
non-computer finishes are retained. The 55 additive details use existing semantic
pivots. Read `../docs/MOTHERBOARD-FINISH-V4.4.md` for rebuild steps and validation.

V4.3 refines only the battery finish: foil laminate variation, graphite grain,
elastomer texture and satin seam/fastener reflections. The preserved intermediate
`assets/aerix-battery-finish-v31.glb` (109.0 MB) is derived from the baseline
below. Geometry, UVs, normals, pivots, animations and all non-battery materials
are unchanged. See `../docs/BATTERY-FINISH-V4.3.md` for the asset audit and rebuild steps.

V4.5 lets the three ascent cards accumulate into a fixed bottom row. The drone
holds the first portrait, shifts to a frontal center view for card two, then
settles at the opposite angle for card three. Earlier cards stay visible and
stationary. Narrow portrait screens use a compact persistent stack. See
`../docs/ASCENT-REFINEMENT-V4.5.md` for timing, framing and validation controls.

V4.1 introduced the three ascent arguments, refined the takeoff portrait and
changed navigation and the header action to Michroma.
The former hero tagline is removed. The later V4 sequence remains intact.
Read `../docs/ASCENT-REFINEMENT-V4.1.md` for the scoped changes and verification.

## Controls for refinement

- Camera, crop and chapter pacing: `js/story.js`.
- Light, source model and optical rendering: `js/scene.js`.
- Atmospheric palette and landscape push: `js/effects.js`.
- Card placement, headline scale, glass finish and accent: `styles.css` V4 block.
- Product arguments: `index.html`.
- Anatomy leader lines, reveal order and responsive placement: `js/anatomy.js`.
- Scroll weight: `main.js`, Lenis duration 1.23 seconds.

Preserve `assets/aerix-quality-v02.glb`: the 94.5 MB asset carries every original map.
The smaller legacy export is not used. New landscape provenance and prompt are in
`../renders/site-v04/image-generation.txt`. The landscape is conceptual imagery,
not a claim about real camera output. Before-V4 source is in `../renders/site-v04/before/`.


V4.10 centers the airborne drone and extends chapter 07 into four landscapes:
glacial heights, evergreen forest, ocean coast, and a pale desert. Scroll blends
the environments while the same 3D aircraft keeps flying; a lower glass caption
panel tracks the journey. New backdrops are stored as native-size lossless WebP.
See `../docs/FLIGHT-WORLDS-V4.10.md` for asset provenance, timing and verification.
The V4.10 verification report records the original landscape preservation checks.

V4.11 adds a closer, curved move into the third ascent portrait, preserves the first
two poses, and gives the active card brighter glass and edge light. The three
cards now have distinct structures: a route motif, a folding-arm count and an
optical detail. All revealed cards retain their fixed positions. See
`../docs/ASCENT-REFINEMENT-V4.11.md` for motion and focus controls.
The V4.11 preservation results are stored with that iteration's evidence.

V4.11.1 adds a quiet architecture note beneath the anatomy introduction: a four-layer
symbol, “Built around each other,” and a short explanation of the shared foundation.
It follows the existing chapter reveal. Compact screens retain their focused layer
panel; the supplemental note appears on wide layouts and the static page. Styling
is in the final V4.11.1 block of `styles.css`; copy is in `index.html`.

V4.12 follows the two motherboard cards with five projected performance callouts.
Radio shielding, processor heat spreading and motion sensing appear on the left;
the M2/M1 memory packages appear on the right. Compact screens use one glass
caption at a time. See `../docs/PERFORMANCE-CALLOUTS-V4.12.md` for timing, targets
and framing controls. Its V4.12 preservation and sequence reports are archived
in `../renders/site-v04-performance/`; that comparison predates V4.13’s optical hold.

V4.13 balances the optical assembly above two glass cards. The left card
introduces the camera; the right diagrams Glass → Iris → Sensor. Both share
a bottom baseline on desktop. Phones read them sequentially in one slot.
The fully open optical study gains 1.6 viewport heights of reading time;
assembly mechanics and the lens entrance keep their accepted choreography.
See `../docs/OPTICAL-BALANCE-V4.13.md` for layout and timing controls.

V4.14 opens the four landscape views with a dark city harbor, followed by mountains,
evergreen and a resort coastline. The centered visor and stronger curved glass
remain through the sequence. The finale brings back the platform and lands the
drone, with four selectable upper-shell colors and a local pre-order configuration
preview. Starting price is a clearly labeled $2,499 USD concept placeholder.
See `../docs/ARRIVAL-FINISHES-V4.14.md` for implementation controls, image provenance,
checkout scope and verification evidence.

V4.14.1 lifts the opening drone/platform composition by 6% of viewport height,
keeping the full platform rim in frame. The adjustment eases into the existing
camera at story 0.38. Hero and early takeoff were visually checked at the reference
1710×990 framing and the hero at 390×844. Before-source and the small framing
review are in `../renders/site-v04-hero-lift/`.

V4.14.2 adds four square finish swatches beside the hero finish name. A fixed-width
name column keeps every swatch stationary as the label changes. The controls share
the existing finish state with the finale and pre-order preview, updating only the
upper-shell colors while preserving the material textures. All four selections
and fixed swatch positions were checked in-browser, plus the 390×844 layout.

V4.14.3 restores Glacial Titanium as a fifth finish and the initial default.
It restores each upper-shell material's original model color independently;
the four tinted finishes, shared selection and original texture maps remain.
An explicitly saved local configuration still restores that chosen finish.

V4.14.4 renames the original finish to Pearl Silver, retaining its saved-selection
identifier and original material colors. The anatomy chapter's left editorial
content sits 40px lower on desktop (32px on phones), aligning its eyebrow with
the inspection link's underline while keeping the link and bottom layer rail fixed.

V4.15 gives the battery chapter two sequential glass cards: the original
closed-cartridge introduction and an exploded-view specification card. The second
card summarizes the four foil cells, single cartridge, sealed pouch construction
and recessed contacts. An extra 0.8 viewport of reading
belongs to the closed pose and 1.8 to the fully open pose; opening and departure
retain their existing camera and animation keys. Forward/reverse card state and
scroll-coordinate verification are in `../renders/site-v04-battery-cards/`.

V4.15.1 replaces the battery's unconfirmed duration with "Flight time target —
Up to 50 min", an illustrative concept specification selected at the user's request.
The benchmark is the published maximum of 45 minutes for the
[DJI Air 3S](https://www.dji.com/air-3s/specs) and 51 minutes for the
[DJI Mavic 4 Pro](https://store.dji.com/ca/product/dji-mavic-4-pro)
(official DJI pages checked September 10, 2026). These are maximum flight-time
claims under DJI's test conditions, not typical endurance or AERIX measurements.
No battery capacity, charging time or tested performance is inferred from them.

V4.16 carries the city image through the physical lens and into the full-screen
flight sequence. The rim holds at story 5.86–6.18 while the centered POV message
appears, then clears before the drone enters. An extra 1.4 viewports belongs to
that lens hold; earlier component studies keep their existing pace. Camera keys
at 7.00, 7.15, 7.26 and 7.40 vary the orbit, lateral placement and distance across
city, mountains, evergreen and coastline, including a closer forest side view.
Portrait framing contains that view and adapts the lens hold to the taller screen.
The final landing composition shifts four percent of the viewport left on desktop;
the original landing mechanics and hero remain unchanged. The year now follows
"Product concept" in the left footer. Timing and visual review are in
`../renders/site-v04-lens-journey/`; camera and hold tuning lives in `js/story.js`.

V4.16.1 makes Titanium Blue the initial finish. All five options remain available,
and an explicitly saved local configuration still restores the selected finish.

V4.16.2 simplifies the folding-arm card: headline, short supporting sentence, then
an understated specification footer with a smaller 04 and a fine divider. The
phone layout follows the same vertical reading order. Scroll focus and camera
choreography are unchanged. Layout reviewed using production markup and CSS at
1710×990, 1280×720, 390×844 and 390×667; all card content fits without overflow.

V4.17 separates the physical city lens from the rounded flight visor. The metal
rim and POV message share an exit at 6.14–6.36; the image opening follows the
camera's perspective so it cannot cover the rim prematurely. Rounded corners
and shader distortion begin only after that exit. The camera backs out while
all 3D rigs are hidden, then the drone enters from outside the viewport over the
mountains. The city overlay and shader background use matching image framing,
with pointer movement deferred until the handoff finishes.

The sequence now has five distinct scenes: city introduction, mountains,
evergreen, resort coastline, and a Times Square-inspired urban aerial. The four
flight scenes retain slow camera movement and the existing centered reticle.
The chapter before flight gains 1.6 viewport heights for the handoff. The new
urban asset and its generation prompt are documented in
`../renders/site-v04-pov-handoff/asset-provenance.md`.
Run `node scripts/web/verify-pov-handoff.mjs` for lens timing, hidden camera
handoff, scene order, and responsive scroll checks. The review toolbar also
offers **Check POV** and **Finish review**, which removes review controls and
the QA query without reloading the model.

V4.17.1 keeps the studio backdrop outside the physical lens through its entrance
and reading hold. The full-screen city prepares at 6.28–6.36, only after the opaque
portal opening covers every viewport corner and before that overlay fades.
Aircraft lighting and the later flight/landing backdrop retain their prior timing.
