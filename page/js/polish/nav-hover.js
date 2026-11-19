// Round 2 (Sam): a hover for the header links that fits the page. The word re-decodes letter
// by letter like the mono telemetry labels, while CSS draws a flight trace under it with a
// glowing dot that flies to the end of the word (refinements.css, "Header link hover").
(() => {
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const GLYPHS = "ABCDEFGHJKLMNPRSTUVXYZ0123456789/<>+#";
  document.querySelectorAll(".site-header nav a").forEach((link) => {
    const text = link.textContent;
    let run = 0;
    link.addEventListener("mouseenter", () => {
      const id = ++run, start = performance.now(), dur = 420;
      const step = (now) => {
        if (id !== run) return;
        const t = Math.min(1, (now - start) / dur), bucket = Math.floor(now / 45);
        link.textContent = [...text].map((ch, i) => {
          const at = (i / text.length) * 0.7;
          return ch === " " || t >= at + 0.3 ? ch : t < at ? ch : GLYPHS[(i * 7 + bucket * 13) % GLYPHS.length];
        }).join("");
        if (t < 1) requestAnimationFrame(step);
        else link.textContent = text;
      };
      requestAnimationFrame(step);
    });
    link.addEventListener("mouseleave", () => { run++; link.textContent = text; });
  });
})();
