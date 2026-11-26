
// Motion pass: element-by-element text, card and drawing reveals behind a viewport scan,
// wireframe scans on the 3D studies and a particle title. Everything keys off chapter entry.
(() => {
    const phaseEl = document.querySelector("#phase-number");
    if (!phaseEl || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const EASE = "cubic-bezier(.2, .75, .15, 1)";
    const SKIP = "[data-flight-number], [data-finish-name], [data-finish-price], .hero-title, fx-w";
    const sections = [...document.querySelectorAll("section.chapter")];
    const clamp01 = x => Math.min(1, Math.max(0, x));
    const onScreen = el => {
        const r = el.getBoundingClientRect();
        if (r.width < 2 || r.height < 2 || r.bottom < 0 || r.top > innerHeight || r.right < 0 || r.left > innerWidth) return false;
        const cs = getComputedStyle(el);
        return cs.visibility !== "hidden" && cs.display !== "none" && +cs.opacity > .05;
    };
    const skipped = el => el.matches(SKIP) || !!el.closest(SKIP) || !!el.querySelector(SKIP);

    // Mono labels decode: each character resolves out of a short glyph scramble, left to right.
    const GLYPHS = "ABCDEFGHJKLMNPRSTUVXYZ0123456789/<>+#";
    const decoding = new Set();
    let ticking = false;
    function tick(now) {
        const bucket = Math.floor(now / 50);
        for (const job of decoding) {
            const t = (now - job.start) / job.dur;
            if (t >= 1) {
                job.nodes.forEach((n, i) => n.data = job.texts[i]);
                decoding.delete(job);
                continue;
            }
            job.nodes.forEach((n, i) => {
                const src = job.texts[i];
                let out = "";
                for (let c = 0; c < src.length; c++) {
                    const ch = src[c], k = job.offsets[i] + c, at = (k / job.total) * .62;
                    out += /\s/.test(ch) ? ch : t < at ? " " : t < at + .26 ? GLYPHS[(k * 7 + bucket * 13) % GLYPHS.length] : ch;
                }
                n.data = out;
            });
        }
        if (decoding.size) requestAnimationFrame(tick);
        else ticking = false;
    }
    function decode(el, delay = 0) {
        if (!/mono/i.test(getComputedStyle(el).fontFamily)) return rise(el, delay);
        for (const job of decoding) if (job.el === el) {
            job.nodes.forEach((n, i) => n.data = job.texts[i]);
            decoding.delete(job);
        }
        const nodes = [], walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
        while (walker.nextNode()) if (walker.currentNode.data.trim()) nodes.push(walker.currentNode);
        if (!nodes.length) return;
        const texts = nodes.map(n => n.data);
        let total = 0;
        const offsets = texts.map(t => (total += t.length) - t.length);
        decoding.add({ el, nodes, texts, offsets, total: Math.max(1, total), start: performance.now() + delay, dur: 520 + Math.min(700, total * 20) });
        nodes.forEach(n => n.data = n.data.replace(/\S/g, " "));
        if (!ticking) {
            ticking = true;
            requestAnimationFrame(tick);
        }
    }

    // Headings rise word by word inside clipped word boxes.
    function words(el, delay = 0) {
        ensureWords(el);
        el.querySelectorAll("fx-w > fx-i").forEach((w, i) => w.animate(
            [{ transform: "translateY(110%)", opacity: 0 }, { transform: "none", opacity: 1 }],
            { duration: 950, delay: delay + i * 55, easing: EASE, fill: "backwards" }));
    }
    function ensureWords(el) {
        if (!el.dataset.fxWords) {
            el.dataset.fxWords = "1";
            const texts = [], walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) texts.push(walker.currentNode);
            texts.forEach(node => {
                if (!node.data.trim()) return;
                const frag = document.createDocumentFragment();
                node.data.split(/(\s+)/).forEach(part => {
                    if (!part) return;
                    if (/^\s+$/.test(part)) return frag.append(" ");
                    const box = document.createElement("fx-w"), inner = document.createElement("fx-i");
                                                inner.textContent = part;
                    box.append(inner);
                    frag.append(box);
                });
                node.replaceWith(frag);
            });
        }
    }

    // Round 2 fix: a transform on a static element makes it the containing block for its
    // absolutely positioned children. The icon tiles in the power card rows sit that way, so
    // sliding the row title moved its icon onto the text until the slide ended, then it jumped.
    // Rows like that fade in place instead.
    const holdsPositioned = el => getComputedStyle(el).position === "static" &&
        [...el.children].some(c => /absolute|fixed/.test(getComputedStyle(c).position));
    const rise = (el, delay = 0) => el.animate(
        getComputedStyle(el).transform === "none" && !holdsPositioned(el)
            ? [{ opacity: 0, transform: "translateY(8px)" }, { opacity: 1, transform: "none" }]
            : [{ opacity: 0 }, { opacity: 1 }],
        { duration: 800, delay, easing: EASE, fill: "backwards" });

    function card(el, delay = 0) {
        let frame = el.querySelector(":scope > .fx-frame");
        if (!frame) {
            if (getComputedStyle(el).position === "static") el.style.position = "relative";
            frame = document.createElement("span");
            frame.className = "fx-frame";
            frame.setAttribute("aria-hidden", "true");
            frame.append(document.createElement("b"));
            el.append(frame);
        }
        el.animate([{ clipPath: "inset(0 0 100% 0)" }, { clipPath: "inset(-14px -14px -14px -14px)" }],
            { duration: 1050, delay, easing: EASE, fill: "backwards" });
        frame.classList.remove("is-beam");
        setTimeout(() => frame.classList.add("is-beam"), delay + 760);
    }

    function tile(el, delay = 0) {
        el.animate([{ opacity: 0, scale: .92 }, { opacity: 1, scale: 1 }],
            { duration: 850, delay, easing: EASE, fill: "backwards" });
        const img = el.querySelector("img");
        img && img.animate([{ clipPath: "inset(100% 0 0 0)" }, { clipPath: "inset(0 0 0 0)" }],
            { duration: 900, delay: delay + 120, easing: EASE, fill: "backwards" });
    }

    function blueprint(wrap, delay = 0) {
        const dur = 1500;
        setTimeout(() => wrap.classList.add("is-scanning"), delay);
        wrap.animate([{ "--fx-scan": "-4%" }, { "--fx-scan": "112%" }], { duration: dur, delay, easing: "cubic-bezier(.45, .05, .3, 1)", fill: "backwards" })
            .finished.then(() => wrap.classList.remove("is-scanning"), () => wrap.classList.remove("is-scanning"));
        wrap.querySelectorAll(".bp-label, .bp-value, .bp-num, .bp-axis").forEach(label => {
            const x = label.style.left ? parseFloat(label.style.left) / 100 : .6;
            rise(label, delay + dur * clamp01(x) * .8 + 60);
        });
        wrap.querySelectorAll(".bp-corner").forEach((c, i) => c.animate([{ opacity: 0, scale: 1.8 }, { opacity: 1, scale: 1 }],
            { duration: 700, delay: delay + i * 70, easing: EASE, fill: "backwards" }));
    }

    function numeral(el, delay = 0) {
        if (el.childElementCount || !/\d/.test(el.textContent)) return;
        const final = el.textContent, digits = final.replace(/\D/g, "").length, start = performance.now() + delay;
        const step = now => {
            const t = (now - start) / 900;
            if (t >= 1) return void (el.textContent = final);
            if (t >= 0) {
                let k = 0;
                el.textContent = final.replace(/\d/g, d => t > (++k) / (digits + 1) ? d : String(Math.floor(now / 60 + k * 3) % 10));
            }
            requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
    }

    const studio = document.createElement("div");
    studio.className = "studio-backdrop";
    studio.setAttribute("aria-hidden", "true");
    studio.innerHTML = '<img src="./assets/worlds/studio-1.webp" alt="" decoding="async"><img src="./assets/worlds/studio-2.webp" alt="" decoding="async">';
    document.body.prepend(studio);
    const STUDIO = { top: [0, .72], ascent: [1, .32], architecture: [1, .55], power: [1, .5], control: [1, .42], optics: [1, .5], finale: [0, .66] };
    function setStudio(id) {
        const [which, alpha] = STUDIO[id] || [-1, 0];
        [...studio.children].forEach((img, i) => {
            img.style.opacity = i === which ? String(alpha) : "0";
        });
    }
    const sweep = document.createElement("div");
    sweep.className = "fx-sweep";
    sweep.setAttribute("aria-hidden", "true");
    document.body.append(sweep);
    const runSweep = () => sweep.animate(
        [{ transform: "translateY(-36vh)", opacity: 0 }, { opacity: 1, offset: .1 }, { opacity: 1, offset: .82 }, { transform: "translateY(106vh)", opacity: 0 }],
        { duration: 1500, easing: "cubic-bezier(.5, .05, .35, 1)" });

    // Round 2 (Sam: "make sure all the cards have some kind of animation, make it consistent").
    // A chapter's reveal used to run once, on chapter entry, so cards that arrive later in the
    // same chapter (the second and third flight cards, "Every detail. Connected.", the power and
    // optics follow-ups, each world caption) were never animated. Now every card runs the same
    // reveal on its own, each time it becomes visible.
    const CARD_SEL = [
        ".flight-card", "[data-power-card]", "[data-control-card]", "[data-optics-card]",
        ".architecture-chapter > .copy", ".pov-chapter > .copy", ".flight-world-panel .world-intro",
        ".world-captions > [data-world]", ".arrival-copy"
    ].join(", ");
    const inCard = el => !!el.closest(CARD_SEL);
    // Visible when the card and every parent up to the page are shown and past `min` opacity.
    // The reveal starts as a card begins to fade in (8%), so scroll-faded cards never show
    // their text first and then blank out. It resets only once the card has fully gone (3%).
    function cardVisible(el, min = .08) {
        const r = el.getBoundingClientRect();
        if (r.width < 2 || r.height < 2 || r.bottom < innerHeight * .04 || r.top > innerHeight * .96 || r.right < 0 || r.left > innerWidth) return false;
        let alpha = 1;
        for (let n = el; n && n !== document.body; n = n.parentElement) {
            const cs = getComputedStyle(n);
            if (cs.display === "none" || cs.visibility === "hidden") return false;
            alpha *= +cs.opacity;
            if (alpha < min) return false;
        }
        return true;
    }
    const glassy = el => {
        const cs = getComputedStyle(el);
        return cs.backdropFilter !== "none" && cs.backdropFilter !== "" || !/rgba?\([^)]*,\s*0\)|transparent/.test(cs.backgroundColor) && cs.backgroundColor !== "rgba(0, 0, 0, 0)";
    };
    // The one card reveal: frame wipe (glass cards), label decode, heading words, numerals,
    // body lines in a stagger, icon tiles and blueprint scans. Same timing for every card.
    const revealLog = [];
    const logReveal = (kind, el) => { revealLog.push({ kind, el: (el.id || el.className || el.tagName).toString().slice(0, 48), phase: phaseEl.textContent, ms: Math.round(performance.now()) }); if (revealLog.length > 200) revealLog.shift(); };
    function revealCard(el) {
        logReveal("card", el);
        const parts = sel => [...el.querySelectorAll(sel)].filter(n => !skipped(n));
        if (glassy(el)) card(el, 0);
        parts(".finish-features li").forEach((n, i) => card(n, 320 + i * 70));
        parts(".eyebrow, .mono:not(.scroll-hint), .anatomy-code, .layer-key li > span, .world-stops em, .optics-path-steps strong").forEach((n, i) => decode(n, 60 + i * 30));
        parts("h2:not([data-fx-particles]), h3:not([data-fx-particles]), .world-name, .optical-title").forEach((n, i) => words(n, 130 + i * 80));
        parts(".power-numbers strong").forEach(n => numeral(n, 220));
        parts("p:not(.eyebrow):not(.mono):not(.world-name):not(.optical-title), dd, dt, .finish-features li > span, .purchase-price > span, .purchase-actions > *, .replay, .layer-key li > strong")
            .forEach((n, i) => rise(n, 280 + Math.min(i, 8) * 45));
        parts("i.ui-tile, i.ui-key").forEach((n, i) => tile(n, 160 + i * 40));
        parts(".bp").forEach(n => blueprint(n, 380));
    }
    const cardOn = new WeakMap();
    function cards() {
        document.querySelectorAll(CARD_SEL).forEach(el => {
            // No wait for the chapter: cardVisible() already multiplies in the chapter's own
            // opacity. Waiting for the chapter to pass 60% let a card fade in fully drawn and
            // then replay its reveal, which read as the card loading twice.
            const was = cardOn.get(el) || false;
            const on = cardVisible(el, was ? .03 : .08);
            cardOn.set(el, on);
            if (on && !was) revealCard(el);
        });
    }

    // The scan front passes each element roughly when its own reveal starts.
    const at = el => 120 + clamp01(el.getBoundingClientRect().top / innerHeight) * 820;
    function reveal(sec) {
        logReveal("section", sec);
        runSweep();
        const seen = new Set();
        // Anything inside a card belongs to that card's own reveal (see cards()).
        const pick = sel => [...sec.querySelectorAll(sel)]
            .filter(el => !seen.has(el) && !skipped(el) && !inCard(el) && onScreen(el))
            .map(el => (seen.add(el), el));
        pick(".flight-card, .power-technical, .optics-cards .copy, .flight-world-panel, .finish-features li").forEach((el, i) => card(el, at(el) + i * 70));
        pick(".eyebrow").forEach(el => decode(el, at(el) + 60));
        pick("h2:not([data-fx-particles]), h3:not([data-fx-particles]), .world-name").forEach(el => words(el, at(el) + 130));
        pick(".power-numbers strong").forEach(el => numeral(el, at(el) + 220));
        pick("p, dd, dt, .finish-features li > span, .purchase-price > span, .purchase-actions > *, .replay").forEach(el => rise(el, at(el) + 280));
        pick("i.ui-tile, i.ui-key, .scroll-cue i").forEach((el, i) => tile(el, at(el) + 160 + i * 40));
        pick(".bp").forEach(el => blueprint(el, at(el) + 380));
    }

    // Projected 3D callouts animate as each one becomes readable.
    const labelOn = new WeakMap();
    function labels() {
        document.querySelectorAll("#model-labels .anatomy-label, #performance-labels .performance-label, #part-labels .part-label").forEach(label => {
            const was = labelOn.get(label) || false;
            const on = parseFloat(label.style.opacity || "0") > (was ? .03 : .08);
            labelOn.set(label, on);
            if (!on || was) return;
            if (label.classList.contains("part-label")) return decode(label, 0);
            label.querySelectorAll(".anatomy-code, .performance-code").forEach(el => decode(el, 0));
            label.querySelectorAll("h3").forEach(el => words(el, 90));
            label.querySelectorAll(".anatomy-note, .performance-note").forEach(el => rise(el, 260));
            label.querySelectorAll(":scope > i.ui-tile").forEach(el => tile(el, 40));
        });
        const heading = document.querySelector("#performance-labels .performance-heading");
        const headingOn = !!heading && getComputedStyle(heading.parentElement).visibility === "visible" && parseFloat(heading.parentElement.style.opacity || "0") > .5;
        if (headingOn && !labelOn.get(heading)) {
            heading.querySelectorAll("p").forEach(el => decode(el, 0));
            heading.querySelectorAll("h3:not([data-fx-particles])").forEach(el => words(el, 120));
        }
        heading && labelOn.set(heading, headingOn);
    }

    // Wireframe scans on the model and the part studies: on entry, then again after idling.
    const scans = { top: "model", architecture: "model", power: "battery", control: "computer", optics: "optics" };
    let lastMove = performance.now(), active = null;
    const scan3d = (id, delay = 450) => setTimeout(() => {
        const key = scans[id];
        if (!key || active !== id || document.body.classList.contains("is-title-revealing")) return;
        window.__aerixFx?.scan(key, { duration: key === "model" ? 2100 : 1700 });
    }, delay);
    setInterval(() => {
        if (active && scans[active] && performance.now() - lastMove > 11000) {
            lastMove = performance.now();
            scan3d(active, 0);
        }
    }, 1000);

    function ping() {
        const node = document.querySelector(".journey-rail li.is-current");
        if (!node) return;
        node.classList.remove("fx-ping");
        requestAnimationFrame(() => node.classList.add("fx-ping"));
        setTimeout(() => node.classList.remove("fx-ping"), 1300);
    }

    // ---- Particle headings: big headings release into particles as their chapter leaves and
    // gather back as it returns. One fixed WebGL layer draws every heading. ----
    const particles = (() => {
        const canvas = document.createElement("canvas");
        canvas.className = "fx-type-layer";
        canvas.setAttribute("aria-hidden", "true");
        const gl = canvas.getContext("webgl", { alpha: true, premultipliedAlpha: true, antialias: false });
        if (!gl) return null;
        document.body.append(canvas);
        const compile = (type, src) => {
            const sh = gl.createShader(type);
            gl.shaderSource(sh, src);
            gl.compileShader(sh);
            return sh;
        };
        const prog = gl.createProgram();
        gl.attachShader(prog, compile(gl.VERTEX_SHADER, `
            attribute vec2 aPos; attribute vec3 aSeed;
            uniform vec2 uRes, uOffset; uniform vec4 uBox; uniform float uDissolve, uIgnite, uDpr, uRise;
            varying float vAlpha;
            void main() {
                float hy = 1.0 - (aPos.y - uBox.y) / uBox.w;
                float rel = clamp(hy, 0.0, 1.0) * .56 + aSeed.x * .24;
                float t = clamp((uDissolve * 1.3 - rel) / .42, 0.0, 1.0);
                vec2 p = aPos + uOffset;
                p.y -= t * t * uRise * (.6 + aSeed.y);
                p.x += sin(aSeed.z * 6.2832 + t * 5.0) * 16.0 * t + (aSeed.x - .5) * 70.0 * t;
                float xr = (aPos.x - uBox.x) / uBox.z;
                float live = step(.001, uIgnite) * step(uIgnite, .999);
                float near = exp(-pow((xr - uIgnite * 1.2 + .1) * 10.0, 2.0)) * live;
                p.y -= near * (4.0 + 16.0 * aSeed.y);
                vAlpha = max(t > 0.0 ? (1.0 - t) * .95 : 0.0, near * (.35 + .65 * aSeed.z));
                gl_PointSize = (1.1 + aSeed.z * 1.7 + near * 1.6) * uDpr;
                gl_Position = vec4(p / uRes * vec2(2.0, -2.0) + vec2(-1.0, 1.0), 0.0, 1.0);
            }`));
        gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, `
            precision mediump float; varying float vAlpha;
            void main() {
                float a = smoothstep(.5, .1, length(gl_PointCoord - .5)) * vAlpha;
                gl_FragColor = vec4(vec3(.78, .9, 1.0) * a, a);
            }`));
        gl.linkProgram(prog);
        if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) return canvas.remove(), null;
        gl.useProgram(prog);
        const loc = n => gl.getUniformLocation(prog, n);
        const U = { res: loc("uRes"), offset: loc("uOffset"), box: loc("uBox"), dissolve: loc("uDissolve"), ignite: loc("uIgnite"), dpr: loc("uDpr"), rise: loc("uRise") };
        const aPos = gl.getAttribLocation(prog, "aPos"), aSeed = gl.getAttribLocation(prog, "aSeed");
        gl.enableVertexAttribArray(aPos);
        gl.enableVertexAttribArray(aSeed);
        gl.enable(gl.BLEND);
        gl.blendFunc(gl.ONE, gl.ONE);
        let dpr = 1;
        const targets = [];
        const make = (el, opts) => ({ el, ...opts, built: false, dissolve: 0, ignite: 0, count: 0, pos: gl.createBuffer(), seed: gl.createBuffer() });
        function resize() {
            dpr = Math.min(2, devicePixelRatio || 1);
            canvas.width = Math.round(innerWidth * dpr);
            canvas.height = Math.round(innerHeight * dpr);
        }
        function build(t) {
            // Build only after the font and the 3D title drum have settled. A
            // rotating face has projected bounds that cannot be used as a text mask.
            if (document.fonts.status !== "loaded" || (t.face &&
                (document.body.classList.contains("is-booting") || document.body.classList.contains("is-title-revealing")))) return false;
            const r = t.el.getBoundingClientRect();
            if (r.width < 10 || r.height < 10) return false;
            const cs = getComputedStyle(t.el), size = parseFloat(cs.fontSize);
            const off = document.createElement("canvas");
            off.width = Math.ceil(r.width + 20);
            off.height = Math.ceil(r.height + 20);
            const ctx = off.getContext("2d");
            ctx.font = `${cs.fontStyle} ${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
            const spacing = cs.letterSpacing === "normal" ? 0 : parseFloat(cs.letterSpacing);
            if ("letterSpacing" in ctx) ctx.letterSpacing = `${spacing}px`;
            ctx.fillStyle = "#fff";
            ctx.textBaseline = "alphabetic";
            // Range measures the browser's actual text run, including flex centering
            // and its font baseline; the element box also contains line-height space.
            const runs = t.face ? [t.el] : [...t.el.querySelectorAll("fx-w > fx-i")];
            for (const run of runs) {
                const range = document.createRange();
                range.selectNodeContents(run);
                const rect = range.getBoundingClientRect(), text = run.textContent.trim();
                const m = ctx.measureText(text);
                const ascent = m.fontBoundingBoxAscent ?? size * .9;
                ctx.fillText(text, rect.left - r.left + 10, rect.top - r.top + 10 + ascent);
            }
            const data = ctx.getImageData(0, 0, off.width, off.height).data, stride = Math.max(2, Math.round(size / 64));
            const pos = [], seed = [];
            for (let y = 0; y < off.height; y += stride)
                for (let x = 0; x < off.width; x += stride)
                    if (data[(y * off.width + x) * 4 + 3] > 140) {
                        pos.push(r.left - 10 + x + (Math.random() - .5) * stride, r.top - 10 + y + (Math.random() - .5) * stride);
                        seed.push(Math.random(), Math.random(), Math.random());
                    }
            t.count = pos.length / 2;
            t.box = [r.left, r.top, r.width, r.height];
            t.base = [r.left, r.top];
            t.rise = Math.max(120, size * 2.2);
            gl.bindBuffer(gl.ARRAY_BUFFER, t.pos);
            gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(pos), gl.STATIC_DRAW);
            gl.bindBuffer(gl.ARRAY_BUFFER, t.seed);
            gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(seed), gl.STATIC_DRAW);
            return (t.built = true);
        }
        function draw() {
            gl.viewport(0, 0, canvas.width, canvas.height);
            gl.clearColor(0, 0, 0, 0);
            gl.clear(gl.COLOR_BUFFER_BIT);
            gl.uniform2f(U.res, innerWidth, innerHeight);
            gl.uniform1f(U.dpr, dpr);
            for (const t of targets) {
                if (!t.count || !((t.dissolve > 0 && t.dissolve < 1) || (t.ignite > 0 && t.ignite < 1))) continue;
                const r = t.el.getBoundingClientRect();
                gl.uniform2f(U.offset, r.left - t.base[0], r.top - t.base[1]);
                gl.uniform4f(U.box, t.box[0], t.box[1], t.box[2], t.box[3]);
                gl.uniform1f(U.dissolve, t.dissolve);
                gl.uniform1f(U.ignite, t.ignite);
                gl.uniform1f(U.rise, t.rise);
                gl.bindBuffer(gl.ARRAY_BUFFER, t.pos);
                gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);
                gl.bindBuffer(gl.ARRAY_BUFFER, t.seed);
                gl.vertexAttribPointer(aSeed, 3, gl.FLOAT, false, 0, 0);
                gl.drawArrays(gl.POINTS, 0, t.count);
            }
        }
        resize();
        addEventListener("resize", () => { resize(); targets.forEach(t => t.built = false); draw(); });
        document.fonts?.ready.then(() => targets.forEach(t => t.built = false));
        const heroFace = document.querySelector("#top .hero-title-face:not(.hero-title-prompt)"), heroTitle = document.querySelector("#top .hero-title");
        heroFace && targets.push(make(heroFace, { mode: "phase", face: true, mask: heroTitle }));
        [["#architecture h2", "#architecture"], ["#performance-labels .performance-heading h3", "#performance-labels"], ["#power .power-technical h3", "#power"], ["#sky h2", "#sky"], ["#finale h2", "#finale"]]
            .forEach(([sel, src]) => {
                const el = document.querySelector(sel), source = document.querySelector(src);
                if (!el || !source) return;
                ensureWords(el);
                el.dataset.fxParticles = "1";
                targets.push(make(el, { mode: "section", source, mask: el }));
            });
        return {
            update(phase) {
                let dirty = false;
                for (const t of targets) {
                    const d = t.mode === "phase"
                        ? clamp01((phase - .015) / .2)
                        : 1 - clamp01(((parseFloat(t.source.style.opacity || getComputedStyle(t.source).opacity) || 0) - .25) / .7);
                    // Round 2 (Sam): once a heading has turned into particles it stays gone.
                    // The mask used to drop at the end of the dissolve, so a section that was
                    // still faintly visible showed its heading again as a ghost.
                    t.mask.classList.toggle("fx-gone", d >= .995);
                    if (!t.built && !(d < .02 && build(t))) {
                        t.dissolve = d;
                        continue;
                    }
                    if (d === t.dissolve) continue;
                    t.dissolve = d;
                    dirty = true;
                    t.mask.style.setProperty("--fx-front", `${Math.round(clamp01((d * 1.3 - .12) / .56) * 100)}%`);
                    t.mask.classList.toggle("fx-dissolving", d > 0 && d < 1);
                }
                dirty && draw();
            },
            ignite() {
                const t = targets.find(x => x.face);
                if (!t || !build(t)) return;
                heroTitle.classList.remove("fx-sheen");
                requestAnimationFrame(() => heroTitle.classList.add("fx-sheen"));
                const start = performance.now();
                const step = now => {
                    t.ignite = clamp01((now - start) / 1500);
                    draw();
                    t.ignite < 1 && requestAnimationFrame(step);
                };
                requestAnimationFrame(step);
            }
        };
    })();
    const title = particles;

    const shown = new Map();
    function loop() {
        lastMove = performance.now();
        const phase = parseFloat(phaseEl.textContent) || 0;
        sections.forEach(sec => {
            const op = parseFloat(sec.style.opacity || getComputedStyle(sec).opacity), was = shown.get(sec) || false;
            // Reveal as the chapter starts to fade in (was 60%), so nothing shows fully drawn first.
            const on = was ? op > .05 : op > .12;
            shown.set(sec, on);
            if (on && !was) {
                active = sec.id || null;
                setStudio(active);
                reveal(sec);
                ping();
                sec.id !== "top" && scan3d(sec.id);
            }
        });
        cards();
        labels();
        const modelLabels = document.querySelector("#model-labels"), layers = ["battery", "thermal", "computer", "tray"];
        if (modelLabels) {
            const key = document.querySelector(".architecture-chapter .layer-key li.is-current");
            const idx = key ? [...key.parentElement.children].indexOf(key) : -1;
            modelLabels.querySelectorAll(".anatomy-label").forEach(l => l.classList.toggle("is-now", idx >= 0 && l.dataset.layer === layers[idx]));
            idx >= 0 ? modelLabels.setAttribute("data-current", layers[idx]) : modelLabels.removeAttribute("data-current");
        }
        title?.update(phase);
    }
    new MutationObserver(loop).observe(phaseEl, { childList: true, characterData: true, subtree: true });

    // The hero plays once the boot overlay has cleared; the title ignites when its drum lands.
    let revealing = document.body.classList.contains("is-title-revealing");
    new MutationObserver(() => {
        const now = document.body.classList.contains("is-title-revealing");
        if (revealing && !now) {
            title?.ignite();
            scan3d("top", 300);
        }
        revealing = now;
    }).observe(document.body, { attributes: true, attributeFilter: ["class"] });
    const boot = setInterval(() => {
        const a = document.querySelector("#awakening");
        if (a && !a.hidden && getComputedStyle(a).display !== "none" && +getComputedStyle(a).opacity > .02) return;
        clearInterval(boot);
        // Start the next geometry stage after the hero reveal; images remain chapter-driven.
        const stream = () => window.__aerixStartStreaming?.();
        "requestIdleCallback" in window ? requestIdleCallback(stream, { timeout: 2500 }) : setTimeout(stream, 1200);
        loop();
        if (!document.body.classList.contains("is-title-revealing")) {
            title?.ignite();
            scan3d("top", 600);
        }
    }, 300);
    // Verification hooks for headless captures.
    window.__aerixMotion = {
        replay: id => {
            const sec = document.getElementById(id);
            if (!sec) return false;
            active = id;
            reveal(sec);
            ping();
            scans[id] && scan3d(id, 200);
            return true;
        },
        ignite: () => (title?.ignite(), !!title),
        card: sel => { const el = document.querySelector(sel); return el ? (revealCard(el), true) : false; },
        log: () => revealLog.slice(),
        tick: () => loop()
    };
})();
