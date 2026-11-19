
// V5 — keeps the journey rail, stepper states and projected-label icons in step with the scroll.
(() => {
    const rail = document.querySelector(".journey-rail");
    const phaseEl = document.querySelector("#phase-number");
    const chapterEl = document.querySelector("#altitude");
    if (!rail || !phaseEl || !chapterEl) return;
    const nodes = [...rail.querySelectorAll("li")];
    const stops = [...document.querySelectorAll(".world-stops li")];
    const sources = [...document.querySelectorAll(".performance-source li")];
    let last = "";
    const tile = name => {
        const holder = document.createElement("i");
        holder.className = "ui-tile";
        holder.setAttribute("aria-hidden", "true");
        const img = document.createElement("img");
        img.src = `./assets/icons/${name}.webp`;
        img.alt = "";
        img.decoding = "async";
        holder.append(img);
        return holder;
    };
    function sync() {
        const phase = parseFloat(phaseEl.textContent) || 0;
        const current = Math.max(0, Math.min(8, parseInt(chapterEl.textContent, 10) || 0));
        const part = sources.findIndex(li => li.getAttribute("aria-current") === "step");
        const stop = stops.findIndex(li => li.classList.contains("is-current"));
        const key = `${phase}|${current}|${part}|${stop}`;
        if (key === last) return;
        last = key;
        rail.style.setProperty("--rail-progress", Math.min(1, phase / 8).toFixed(4));
        // Drum: the current chapter stays pinned while the strip scrolls. On the hero the
        // strip eases in from a centred overview so the whole itinerary is visible first.
        const settle = Math.min(1, Math.max(0, phase / 1.1));
        const ease = settle * settle * (3 - 2 * settle);
        rail.style.setProperty("--rail-e", (4 * (1 - ease) + phase * ease).toFixed(3));
        document.body.classList.toggle("ui-open-sky", phase >= 6.85);
        // At the finale the rail lifts so its last node clears the launch platform.
        document.body.classList.toggle("ui-finale", phase >= 7.6);
        // Per-chapter rail geometry [node pitch px, vertical offset vh] keeps the rail clear of
        // each chapter's content: shorter above the optics cards, lifted over the finale platform.
        const railLayout = innerWidth <= 760 ? [30, 0]
            : [[55, -3.7], [50, -6.6], [52, 0], [52, 0], [52, 0], [46, -9.9], [52, 0], [47, -3.96], [38, -18]][current];
        rail.style.setProperty("--rail-gap", `${railLayout[0]}px`);
        rail.style.setProperty("--rail-shift", `${railLayout[1]}vh`);
        nodes.forEach((li, i) => {
            li.classList.toggle("is-current", i === current);
            li.classList.toggle("is-complete", i < current);
            if (i === current) li.firstElementChild.setAttribute("aria-current", "step");
            else li.firstElementChild.removeAttribute("aria-current");
        });
        const atHero = phase < .32;
        rail.classList.toggle("is-overview", atHero);
        document.body.classList.toggle("ui-at-hero", atHero);
        stops.forEach((li, i) => li.classList.toggle("is-passed", i < stop));
        // Anatomy bars fill across their own layer's scroll segment (the bundle's anatomy
        // boundaries, ending where the chapter hands over), so the active bar shows real progress.
        const layerBounds = [1.995, 2.05, 2.105, 2.16, 2.245];
        document.querySelectorAll(".architecture-chapter .layer-key li").forEach((li, i) => {
            const fill = Math.min(1, Math.max(0, (phase - layerBounds[i]) / (layerBounds[i + 1] - layerBounds[i])));
            li.style.setProperty("--layer-fill", fill.toFixed(3));
            li.classList.toggle("is-ahead", fill <= 0);
        });
        // A step lights only once its callout is readable, so the indicator never runs ahead.
        const shown = [...document.querySelectorAll("#performance-labels .performance-label")]
            .filter(label => parseFloat(label.style.opacity || "0") > .45).length;
        document.querySelectorAll(".performance-steps span").forEach((step, i) => step.classList.toggle("is-lit", i < shown));
        updateParts(phase);
    }

    // Part callouts projected from the live battery and optics study models.
    const partSets = [
        { set: "battery", from: 3.28, to: 3.5, layout: "left", items: [
            ["BATTERY_LID_ROOT", "Lid"],
            ["CELL_2_ROOT", "Cells 01—04"],
            ["BATTERY_SIDE_COVER_ROOT", "Housing", { low: true }]
        ] },
        // Sam, Nov 19: the lens retracts from 5.28, so its callouts are gone by 5.30
        // (they used to stay to 5.62 and the leaders piled onto each other).
        { set: "optics", from: 5.08, to: 5.3, fadeOut: .035, layout: "above", items: [
            ["OPTICS_WINDOW_REVEAL_ROOT", "Front element"],
            ["OPTICS_REAR_CELL_REVEAL_ROOT", "Rear element"],
            ["OPTICS_IRIS_REVEAL_ROOT", "Iris"],
            ["OPTICS_IR_CUT_FILTER_ROOT", "Filter"],
            ["OPTICS_CMOS_SENSOR_ROOT", "Sensor", { dx: -56, dy: -14 }]
        ] }
    ];
    const SVG_NS = "http://www.w3.org/2000/svg";
    const partRoot = document.createElement("div");
    partRoot.id = "part-labels";
    partRoot.setAttribute("aria-hidden", "true");
    const partSvg = document.createElementNS(SVG_NS, "svg");
    partSvg.classList.add("part-leaders");
    partRoot.append(partSvg);
    (document.querySelector("#visual-stage") || document.body).append(partRoot);
    const partGroups = partSets.map(group => {
        const layer = document.createElementNS(SVG_NS, "g");
        const guide = document.createElementNS(SVG_NS, "path");
        guide.classList.add(group.layout === "above" ? "part-axis" : "part-dimension");
        layer.append(guide);
        partSvg.append(layer);
        const items = group.items.map(([name, text, opts = {}]) => {
            const path = document.createElementNS(SVG_NS, "path");
            const dot = document.createElementNS(SVG_NS, "circle");
            dot.setAttribute("r", "5");
            layer.append(path, dot);
            const label = document.createElement("span");
            label.className = "part-label";
            label.textContent = text;
            partRoot.append(label);
            return { name, text, opts, path, dot, label, width: 0 };
        });
        return { ...group, layer, guide, items };
    });
    const ramp = (x, a, b) => Math.min(1, Math.max(0, (x - a) / (b - a)));
    const labelWidth = item => item.width || (item.width = item.label.offsetWidth) || item.text.length * 9.4;
    const extreme = (points, pick) => points.reduce((best, point) => pick(point, best) ? point : best);
    function hideGroup(group) {
        group.layer.style.opacity = "0";
        group.items.forEach(item => item.label.style.opacity = "0");
    }
    function updateParts(phase) {
        const project = window.__aerixProjectPart;
        partSvg.setAttribute("viewBox", `0 0 ${innerWidth} ${innerHeight}`);
        partGroups.forEach(group => {
            const alpha = project && innerWidth >= 1100
                ? ramp(phase, group.from, group.from + .06) * (1 - ramp(phase, group.to - (group.fadeOut || .06), group.to))
                : 0;
            if (alpha <= 0) return hideGroup(group);
            const hits = group.items.map(item => ({ item, p: project(group.set, item.name) }));
            if (hits.some(hit => !hit.p)) return hideGroup(group);
            group.layer.style.opacity = String(alpha);
            group.items.forEach(item => item.label.style.opacity = String(alpha));
            if (group.layout === "left") layoutLeft(group, hits, project);
            else layoutAbove(group, hits);
        });
    }
    function place(item, x, y, anchor, from) {
        item.label.style.transform = `translate3d(${x.toFixed(1)}px, ${(y - 10).toFixed(1)}px, 0)`;
        item.path.setAttribute("d", from);
        item.dot.setAttribute("cx", anchor.x.toFixed(1));
        item.dot.setAttribute("cy", anchor.y.toFixed(1));
    }
    function layoutLeft(group, hits, project) {
        const column = Math.max(40, innerWidth * .1);
        let floor = 112;
        hits.sort((a, b) => a.p.center.y - b.p.center.y).forEach(({ item, p }) => {
            // Low parts are labelled from below so the leader never crosses the part itself.
            const low = item.opts.low;
            const edge = extreme(p.corners, low ? (a, b) => a.y > b.y : (a, b) => a.x < b.x);
            const anchor = { x: edge.x + (p.center.x - edge.x) * .28, y: edge.y + (p.center.y - edge.y) * .28 };
            const y = Math.max(floor, Math.min(innerHeight - 48, anchor.y + (low ? 34 : -24)));
            floor = y + 52;
            const end = column + labelWidth(item) + 14;
            const bend = Math.max(end + 24, anchor.x - (low ? 30 : 64));
            place(item, column, y, anchor, `M ${end} ${y} L ${bend} ${y} L ${anchor.x.toFixed(1)} ${anchor.y.toFixed(1)}`);
        });
        // Height of the four-cell stack, dimensioned beside it with end ticks and arrowheads.
        const cells = ["BAT29_POUCH_CELL_1", "BAT29_POUCH_CELL_4"].map(name => project(group.set, name)).filter(Boolean);
        if (cells.length < 2) return group.guide.setAttribute("d", "");
        const top = Math.min(cells[0].center.y, cells[1].center.y) - 14;
        const bottom = Math.max(cells[0].center.y, cells[1].center.y) + 14;
        const x = Math.max(...cells.flatMap(cell => cell.corners.map(corner => corner.x))) + 16;
        group.guide.setAttribute("d", `M ${x} ${top} L ${x} ${bottom} M ${x - 8} ${top} L ${x + 8} ${top} M ${x - 8} ${bottom} L ${x + 8} ${bottom} M ${x - 4} ${top + 8} L ${x} ${top} L ${x + 4} ${top + 8} M ${x - 4} ${bottom - 8} L ${x} ${bottom} L ${x + 4} ${bottom - 8}`);
    }
    function layoutAbove(group, hits) {
        let lastRight = -Infinity, lifted = false;
        hits.sort((a, b) => a.p.center.x - b.p.center.x).forEach(({ item, p }) => {
            const top = extreme(p.corners, (a, b) => a.y < b.y);
            const anchor = p.center;
            const width = labelWidth(item);
            const x = Math.max(24, anchor.x - width * .5 - 20 + (item.opts.dx || 0));
            lifted = x < lastRight + 18 ? !lifted : false;
            const y = Math.max(112, top.y - 56 - (lifted ? 28 : 0) + (item.opts.dy || 0));
            lastRight = x + width;
            place(item, x, y, anchor, `M ${(x + width * .5).toFixed(1)} ${y + 14} L ${anchor.x.toFixed(1)} ${anchor.y.toFixed(1)}`);
        });
        const first = hits[0].p.center, last = hits[hits.length - 1].p.center;
        const dx = last.x - first.x || 1, t = (70 - first.x) / dx;
        group.guide.setAttribute("d", `M ${(first.x + dx * t).toFixed(1)} ${(first.y + (last.y - first.y) * t).toFixed(1)} L ${last.x.toFixed(1)} ${last.y.toFixed(1)}`);
    }
    const watch = el => new MutationObserver(sync).observe(el, { childList: true, characterData: true, subtree: true });
    watch(phaseEl);
    watch(chapterEl);
    sync();

    const anatomyIcons = { battery: "battery-pack", thermal: "fins", computer: "chip-pins", tray: "tray" };
    const performanceIcons = { radio: "tower-shield", processor: "chip-heat", imu: "gyroscope", m2: "chip-pins", m1: "chip-swap" };
    function decorate() {
        document.querySelectorAll("#model-labels .anatomy-label[data-layer]:not(.has-tile)").forEach(label => {
            const icon = anatomyIcons[label.dataset.layer];
            if (!icon) return;
            label.classList.add("has-tile");
            label.prepend(tile(icon));
        });
        document.querySelectorAll("#performance-labels .performance-label[data-part]:not(.has-tile)").forEach(label => {
            const icon = performanceIcons[label.dataset.part];
            if (!icon) return;
            label.classList.add("has-tile");
            label.prepend(tile(icon));
        });
        const heading = document.querySelector("#performance-labels .performance-heading");
        if (heading && !heading.querySelector(".performance-steps")) {
            const steps = document.createElement("div");
            steps.className = "performance-steps";
            steps.setAttribute("aria-hidden", "true");
            sources.forEach((_, i) => {
                const step = document.createElement("span");
                step.textContent = String(i + 1).padStart(2, "0");
                steps.append(step);
            });
            heading.append(steps);
            last = "";
            sync();
        }
    }
    ["#model-labels", "#performance-labels"].forEach(selector => {
        const root = document.querySelector(selector);
        if (root) new MutationObserver(decorate).observe(root, { childList: true });
    });
    decorate();
})();
