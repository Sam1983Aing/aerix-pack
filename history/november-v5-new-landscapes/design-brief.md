# V4.2 — Rolodex hero title

After the optical loader, hold the drone on the platform while READY FOR? rotates
around a shared horizontal axis to TAKE OFF, then ASCENT. Use Michroma, a brief
pause on each face, shaded 3D turns, and the original final title size and position.
Keep the page at story zero until the reveal completes; navigation and Skip reveal
finish it immediately. Refresh replays both stages. No changes to model quality,
takeoff, flight cards, or later component chapters. Before-state: renders/site-v04-title/before/.

# V4.1 — Held flight / September 10 refinement

Continue the approved Glacial Titanium direction. Preserve takeoff through the close lens
approach, then hold a large front three-quarter drone portrait with visible lens and fast
rotor discs. Gentle positional hover only while three equally weighted glass cards pass
through a feathered horizontal mask, one at a time. Keep every later component chapter.
Cards: freedom of perspective; folding airframe; suspended camera. No invented specs.
Michroma navigation and header explore action. Remove the hero tagline and motion toggle.
Cinematic is the sole selectable experience, including on mobile; honor the OS reduced-motion
setting and keep readable content if WebGL is unavailable. Refresh always replays the intro.
Original source quality remains immutable. Before-state: renders/site-v04-ascent/before/.

# V4 — Glacial Titanium

Full WebGL product campaign. Precise, expansive, tactile, quietly confident.
Palette: midnight blue graphite #0b111a, ice blue #aacde8, silver white #edf2f7.
Instrument Sans headlines; Michroma brand; IBM Plex Mono annotations.
Motion: weighted expo-out scroll, reversible authored cameras, slow stabilization.
Every component keeps a persuasive role and a substantial shot. Vary composition,
not importance. No invented camera, endurance, safety or durability specifications.
Signature: sculptural full-width architecture and an optical portal into a glacial landscape.
Selective floating glass cards overlay the opaque product. Final shot is a close front
three-quarter portrait. All approved model geometry, maps and animation pivots stay intact.

# AERIX / V3 — Ascent

Direction: poised, deliberate, sculptural. Graphite, copper, sage and ivory. The full-quality V27 exterior / V30 interior remains the product. One consistent Instrument Sans treatment within each section headline, with the Michroma hero identity retained.

The sequence is a gradual takeoff, a full orbital flight through side/rear/underside views, a held exploded architecture, physical reassembly and a return to flight. Separate detail studies enter in a vertical procession after the airframe closes. The camera enters a completely reassembled lens and emerges into a focused front three-quarter sky shot. Give each of these beats its own scroll duration.

Rendering contract: the atmosphere is behind the HTML; opaque product geometry is above it. No scroll-driven transparency on solid parts. The hero title fades at its projected meeting with the platform. Components move out of view before hiding. Optical transmission samples a proper linear-space atmosphere. Preserve source texture maps and geometry; the studies share the same master asset.

Current implementation and checks: `../docs/CINEMATIC-REFINEMENT-V3.md`. Runtime controls are `js/story.js`, `js/flight.js`, `js/scene.js` and `js/effects.js`. Before-state files are in `../renders/site-v03/before/`.

---

# Previous V2 direction

Approved direction: awaken, depart, suspend, inspect, cross the lens, emerge.

Forward browser scroll advances upward through the scene. Outgoing copy moves down;
new copy arrives from above. A stationary circular launch platform gives the first
metres of ascent a physical reference. Small stabilization movements continue in flight.
The rotors blend from visible blades into translucent exposure discs, with no discrete
blades at cruise speed.

The palette begins in carbon, graphite and copper, then opens into a sage atmosphere
and a warm ivory horizon. Michroma adds a wide technical cadence; Instrument Sans
keeps the body copy and large supporting headlines human and readable. No invented
product specifications or simulated altitude measurements: the side gauge indicates
chapters 00–08.

The nine stops: pre-flight; vertical departure; suspended architecture; battery;
flight computer; optical assembly; first-person perspective; open sky; departure/CTA.
The optical passage uses the real camera assembly, a short aperture transition and
a refracted atmospheric shader. Typography remains crisp inside the subtle glass frame.

## Art direction controls

- `js/story.js`: deterministic chapter poses, framing, ascent, rotor/sky/optical envelopes.
- `js/anchors.js`: stable assembly and lens targets in metres, fixed master-model offset.
- `js/scene.js`: lighting, semantic material isolation, camera, flight rig, explorer.
- `js/effects.js`: machined platform, atmospheric light/clouds, rotor exposure shader.
- `styles.css`: typography, reverse-moving copy, optical framing, static/mobile layouts.
- `main.js`: one GSAP clock, Lenis, intro/skip, navigation, motion preferences, explorer.

## Component replacement contract

The GLB retains the original master v30 assembly roots and animation clips. The V2
flight rig wraps the model; rotor spin wraps the existing propeller children. Cameras
use authored anchors, never the current mesh bounding boxes. Materials and geometry
beneath a semantic root may be refined while preserving its name, transforms, scale
and animation pivots. Camera coordinates and scroll poses then remain unchanged.
Larger physical proportions still require a local fit/occlusion review. A prerecorded
video would need to be rendered again after a visible model change.

V1 is preserved at `../site-v1/`. The native Blender master and exported model are
unchanged. This iteration uses the same object for the final departure; no generated
video is required or presented as real-time 3D.

## Progressive rendering

Desktop starts with an optional, skippable optical initialization. Actual GLB byte
progress is followed by a calibration phase while geometry/shaders prepare. Repeat
visits in the same tab skip the cinematic introduction. Motion can be disabled.
Mobile, reduced-motion, JavaScript-disabled and render-failure paths use normal
readable poster sections. Mobile and reduced-motion visitors may explicitly open
the manual 3D explorer. Offscreen rendering stops while the document is hidden.

## V2.1 quality refinement — September 9

Preserve the approved V27 exterior and V30 interior geometry/materials. Replace the
lossy runtime with a complete-detail derivative; batch static geometry only. Enlarge
the hero approximately 11%, keep the ascent and later views, and refine the platform
with rounded dark metal, a copper inlay and restrained studio highlights. Quality
review includes component macro views around all sides, not only full-page captures.

## V2.2 flight direction

Reference: https://drone.riotters.com/?utm_source=lenis . Adopt the visible combination
of banking, turning, cross-frame travel and settling. Add a restrained continuous
hover to airborne chapters, with a small damped scroll response. Keep grounded hero
contact and stop added motion before exploded inspection. Retain the approved asset,
platform, palette, typography and ascent structure. Controls live in `js/flight.js`.
