
// Shader buttons: the primary button fills with slow liquid titanium light; outline and round
// buttons get a shader-drawn hairline rim with a travelling light and a pointer glow. Each draws
// in its own small canvas behind the label, only while on screen, at 30fps unless hovered.
(() => {
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const SELECTORS = [
        [".purchase-actions .pill-button", 0],
        [".purchase-actions .detail-button", 1],
        [".header-explore > span", 1],
        ["body.is-live .architecture-chapter .text-link span", 1],
        [".optics-overview .detail-note i.ui-tile", 1],
        [".scroll-cue i", 1]
    ];
    const VERT = "attribute vec2 aPos; varying vec2 vUv; void main() { vUv = aPos * .5 + .5; gl_Position = vec4(aPos, 0.0, 1.0); }";
    const FRAG = `
        precision mediump float;
        uniform vec2 uSize, uPointer; uniform float uTime, uHover, uKind, uRadius, uDpr;
        varying vec2 vUv;
        float box(vec2 p, vec2 b, float r) { vec2 q = abs(p) - b + r; return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r; }
        float hash(vec2 p) { return fract(sin(dot(p, vec2(41.3, 289.1))) * 43758.5453); }
        float noise(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
            return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + 1.0), f.x), f.y); }
        float fbm(vec2 p) { float v = 0.0, a = .5; for (int i = 0; i < 4; i++) { v += a * noise(p); p *= 2.03; a *= .5; } return v; }
        void main() {
            vec2 px = vec2(vUv.x, 1.0 - vUv.y) * uSize;
            vec2 c = px - uSize * .5;
            float aa = 1.0 / uDpr;
            float d = box(c, uSize * .5 - aa * .5, uRadius);
            float inside = 1.0 - smoothstep(-aa, 0.0, d);
            float glow = exp(-length(px - uPointer) / (34.0 + 26.0 * uHover));
            float rim = 1.0 - smoothstep(0.0, aa * 1.1, abs(d + aa * .5));
            if (uKind < .5) {
                vec2 q = px / 86.0;
                float t = uTime * (.07 + .16 * uHover);
                float n = fbm(q + vec2(t, -t * .6) + fbm(q * 1.6 - vec2(t * .8, t)));
                vec3 col = mix(vec3(.64, .81, .97), vec3(.86, .94, 1.0), smoothstep(.25, .8, n));
                float lines = 1.0 - smoothstep(0.0, .035, abs(fract(n * 4.0 + t) - .5) - .44);
                col += vec3(.75, .88, 1.0) * lines * .07;
                col += vec3(1.0) * glow * (.22 + .35 * uHover);
                float sheen = pow(max(0.0, 1.0 - abs(vUv.x - fract(uTime * .09) * 1.6 + .3) * 3.0), 6.0);
                col += vec3(1.0) * sheen * .18;
                col = mix(col, vec3(1.0), rim * .35);
                gl_FragColor = vec4(col * inside, inside);
            } else {
                float ang = atan(c.y, c.x);
                float travel = pow(.5 + .5 * cos(ang - uTime * (.7 + 1.6 * uHover)), 14.0);
                float edge = rim * (.26 + .74 * travel + .4 * uHover);
                float fill = inside * (glow * (.1 + .22 * uHover) + (1.0 - vUv.y) * .05);
                vec3 col = vec3(.72, .87, 1.0) * edge + vec3(.42, .68, 1.0) * fill;
                float a = clamp(edge + fill, 0.0, 1.0);
                gl_FragColor = vec4(col, a);
            }
        }`;
    const buttons = [];
    function attach(el, kind) {
        if (el.dataset.shaderButton) return;
        const canvas = document.createElement("canvas");
        const gl = canvas.getContext("webgl", { alpha: true, premultipliedAlpha: true, antialias: false });
        if (!gl) return;
        el.dataset.shaderButton = String(kind);
        canvas.className = "shader-button-canvas";
        canvas.setAttribute("aria-hidden", "true");
        if (getComputedStyle(el).position === "static") el.style.position = "relative";
        el.prepend(canvas);
        const compile = (type, src) => { const sh = gl.createShader(type); gl.shaderSource(sh, src); gl.compileShader(sh); return sh; };
        const prog = gl.createProgram();
        gl.attachShader(prog, compile(gl.VERTEX_SHADER, VERT));
        gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, FRAG));
        gl.linkProgram(prog);
        if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) { canvas.remove(); delete el.dataset.shaderButton; return; }
        gl.useProgram(prog);
        const buf = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, buf);
        gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
        const loc = gl.getAttribLocation(prog, "aPos");
        gl.enableVertexAttribArray(loc);
        gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
        const u = n => gl.getUniformLocation(prog, n);
        const b = { el, kind, canvas, gl, u: { size: u("uSize"), pointer: u("uPointer"), time: u("uTime"), hover: u("uHover"), kind: u("uKind"), radius: u("uRadius"), dpr: u("uDpr") },
            w: 0, h: 0, hover: 0, target: 0, px: -999, py: -999, last: 0 };
        el.addEventListener("pointerenter", () => b.target = 1);
        el.addEventListener("pointerleave", () => { b.target = 0; b.px = b.py = -999; });
        el.addEventListener("pointermove", e => { const r = el.getBoundingClientRect(); b.px = e.clientX - r.left; b.py = e.clientY - r.top; });
        el.classList.add("has-shader");
        buttons.push(b);
    }
    function scanForButtons() {
        SELECTORS.forEach(([sel, kind]) => document.querySelectorAll(sel).forEach(el => attach(el, kind)));
    }
    const visible = el => {
        const r = el.getBoundingClientRect();
        if (r.width < 4 || r.bottom < 0 || r.top > innerHeight || r.right < 0 || r.left > innerWidth) return null;
        let node = el;
        while (node && node !== document.body) {
            const cs = getComputedStyle(node);
            if (cs.visibility === "hidden" || cs.display === "none" || +cs.opacity < .02) return null;
            node = node.parentElement;
        }
        return r;
    };
    let frame = 0, visibleSet = new Set();
    setInterval(() => { visibleSet = new Set(buttons.filter(b => visible(b.el))); }, 400);
    function tick(now) {
        frame++;
        for (const b of visibleSet) {
            b.hover += (b.target - b.hover) * .12;
            if (b.hover < .02 && frame % 2) continue;
            const r = b.el.getBoundingClientRect(), dpr = Math.min(2, devicePixelRatio || 1);
            const w = Math.round(r.width * dpr), h = Math.round(r.height * dpr);
            if (w !== b.w || h !== b.h) { b.w = b.canvas.width = w; b.h = b.canvas.height = h; }
            const { gl, u } = b;
            gl.viewport(0, 0, w, h);
            const cs = getComputedStyle(b.el), radius = cs.borderRadius.includes("%") ? Math.min(r.width, r.height) / 2 : Math.min(parseFloat(cs.borderRadius) || 0, Math.min(r.width, r.height) / 2);
            gl.uniform2f(u.size, r.width, r.height);
            gl.uniform2f(u.pointer, b.px < -900 ? r.width * .78 : b.px, b.py < -900 ? -r.height * .6 : b.py);
            gl.uniform1f(u.time, now / 1000);
            gl.uniform1f(u.hover, b.hover);
            gl.uniform1f(u.kind, b.kind);
            gl.uniform1f(u.radius, radius);
            gl.uniform1f(u.dpr, dpr);
            gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
        }
        requestAnimationFrame(tick);
    }
    scanForButtons();
    setTimeout(scanForButtons, 2500);
    requestAnimationFrame(tick);
})();
