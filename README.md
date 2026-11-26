# AERIX, the free pack

The landing page, the 3D drone and every prompt from my video **[Is GPT Astra 6.2 Better? A Blender Drone and a 3D Landing Page](https://youtu.be/JVO5MSEi2LI)**, sponsored by Higgsfield.

**Open it online:** https://sam1983aing.github.io/aerix-pack/

![The AERIX free pack: the landing page, the RILL model, the vocabulary and the prompts](sheets/shots/pack-preview.jpg)

Or download the repo and open `index.html`. Everything also opens from your disk, no install needed.

## What's inside

| | Where | What it is |
|---|---|---|
| The landing page | `AERIX.html` | The AERIX page as one file. Double-click it. Online: [the live page](https://sam1983aing.github.io/aerix-pack/page/). |
| Its source | `page/` | The same page as plain HTML, CSS and JavaScript, no build step. |
| The AERIX model | `page/assets/model/` | The drone on the landing page, built in Blender with GPT-6 Astra in September. |
| Its Blender scripts | `model/aerix/blender-scripts/` | The Python scripts that built AERIX, from the grey blockout to the finished interior. |
| Its concept images | `model/aerix/concepts/` | The three AI concepts it started from, with the prompt for each. |
| The RILL model | `model/RILL-viewer.html`, `model/rill.glb` | The drone GPT-6.2 Astra built in Blender, with its fold animation. |
| RILL's Blender scripts | `model/blender-scripts/` | The Python scripts that built RILL, one per version from V01 to V18, with the checks and reviews between them. |
| Every version of the page | `history/` | The code of each version, September V1 to V4.17.1 and November v1 to v6, so you can follow how the page grew. |
| Vocabulary | `sheets/vocabulary.html` | 21 techniques from the page with a copy-paste prompt for each. |
| Prompts | `sheets/prompts.html` | The starter prompt, the Higgsfield world prompts with settings and cost, and every message that built RILL. |

## Run the source

`AERIX.html` works by double-click. The `page/` folder uses JavaScript modules, so serve it:

```bash
cd page
python3 -m http.server 8000
```

Then open http://localhost:8000. The page is plain HTML, CSS and JavaScript with three.js, GSAP and Lenis, and no build step.

## The worlds behind the drone

In the video, each world is a 5 second clip made with Seedance 2.5 on Higgsfield and upscaled to 4K. Those clips stay with the video, so the page here uses the September stills and doesn't wait on any clip. The prompts that made them are in `sheets/prompts.html`.

To bring video back, put a 16:9 MP4 in `page/assets/worlds/clips/` and set `clip:'worlds/clips/your-clip.mp4'` on that world in `page/js/flight-worlds.js`. The page then plays it when the world fades in, and the scroll waits for it to finish.

## How the page is put together

- `page/main.js` holds the scroll and the story clock: one number from 0 to 8 drives everything.
- `page/js/scene.js` is the 3D scene: the model, the studies, the camera and the render loop.
- `page/js/effects.js` draws the sky and the worlds and plays the clips. `page/js/flight-worlds.js` lists the worlds.
- `page/js/polish/` holds the motion layer: card reveals, text decode, the particle title (`motion.js`), part labels (`ui-refresh.js`), the menu hover (`nav-hover.js`).
- `page/js/part-pins.js` draws the numbered pins. `page/js/finishes.js` lists the five finishes.
- `page/assets/model/` is the AERIX drone, split so a light version shows first and the rest streams in (`manifest.json`).

## The two drones and their scripts

**AERIX** is the drone on the landing page. It started from one AI concept image (the three options are in `model/aerix/concepts/`), and GPT-6 Astra built it in Blender in September: a grey blockout, then the outside, then the folding arms, the battery, the flight core and the interior, each step a script in `model/aerix/blender-scripts/`. The finished model is the one the page streams from `page/assets/model/`.

**RILL** was built two months later from the measurements of a real foldable camera drone, then given its own design and name. The scripts show how GPT-6.2 Astra built it, version by version, from a grey blockout to the finished outside. The viewer shows V14c, and V15 to V18 carry on with the shell, the finish and the artwork.

Both sets of scripts expect the project's folder layout and reference files, which aren't included, so read them to learn the method rather than to run them as they are. Blender 5.2.

## Every version of the page

`history/` keeps the code of every saved version, in order:

- `september-v1` to `september-v3`, then `september-v4.17.1`: the first page, built with GPT-6 Astra.
- `november-v1-threeui-port`: the September page with its ThreeUI polish.
- `november-v2-leader-demos` to `november-v6-4k-clips`: leader lines, the world clips, numbered pins and card reveals, round by round. `november-v6` is the page in `page/`, with video worlds.

It's code only (HTML, CSS and JavaScript). The models, images and libraries live once in `page/`, so open these folders to read and compare, and run the page from `page/`.

## Credits and licences

- The code of the page and the viewer: MIT (`LICENSE`).
- [three.js](https://threejs.org) (MIT), [GSAP](https://gsap.com) (GSAP's standard licence, free), [Lenis](https://lenis.darkroom.engineering) (MIT, `page/vendor/LENIS-LICENSE`), [Draco](https://google.github.io/draco/) (Apache 2.0, `page/vendor/draco/LICENSE`).
- Fonts: Michroma, Instrument Sans and IBM Plex Mono, under the SIL Open Font License (`page/assets/fonts/`).
- The AERIX and RILL models are mine, built with GPT-6 Astra and GPT-6.2 Astra. Use them to learn and to build your own pages.

## Find me

[YouTube](https://youtu.be/JVO5MSEi2LI) · [X](https://x.com/SammmAing) · [LinkedIn](https://www.linkedin.com/in/samnang-aing-639168341/) · [Threads](https://www.threads.com/@prompting_lab/) · [Instagram](https://www.instagram.com/samnang.aing/)
