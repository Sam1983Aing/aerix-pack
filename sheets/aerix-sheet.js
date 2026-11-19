
const GLYPHS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/#';
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
function decode(el, ms = 520) {
  if (reduce || el.dataset.busy) return;
  const text = el.dataset.text || (el.dataset.text = el.textContent);
  el.dataset.busy = '1';
  const start = performance.now();
  const tick = now => {
    const p = Math.min(1, (now - start) / ms), fixed = Math.floor(p * text.length);
    el.textContent = [...text].map((c, i) => i < fixed || c === ' ' ? c : GLYPHS[Math.random() * GLYPHS.length | 0]).join('');
    if (p < 1) requestAnimationFrame(tick); else { el.textContent = text; delete el.dataset.busy; }
  };
  requestAnimationFrame(tick);
}
const seen = new IntersectionObserver(entries => entries.forEach(e => { if (e.isIntersecting) { decode(e.target); seen.unobserve(e.target); } }), { threshold: .6 });
document.querySelectorAll('.label, .mono').forEach(el => { if (!el.querySelector('*')) seen.observe(el); });
document.querySelectorAll('nav.sheets a').forEach(a => a.addEventListener('mouseenter', () => decode(a, 380)));
async function copyText(text) {
  try { await navigator.clipboard.writeText(text); return true; } catch {}
  const area = document.createElement('textarea'); area.value = text; area.style.position = 'fixed'; area.style.opacity = '0';
  document.body.append(area); area.select(); let ok = false; try { ok = document.execCommand('copy'); } catch {} area.remove(); return ok;
}
document.querySelectorAll('button.copy').forEach(b => b.addEventListener('click', async () => {
  const pre = b.closest('.prompt').querySelector('pre');
  const ok = await copyText(pre.textContent);
  b.textContent = ok ? 'Copied' : 'Select and copy'; b.classList.toggle('done', ok);
  setTimeout(() => { b.textContent = 'Copy prompt'; b.classList.remove('done'); }, 1800);
}));
// Online, the landing page opens from its source folder, which streams in faster than the one-file version.
if (location.protocol.startsWith('http')) document.querySelectorAll('[data-online]').forEach(a => { a.href = a.dataset.online; });
const box = document.querySelector('.lightbox');
if (box) {
  document.querySelectorAll('figure img').forEach(img => img.addEventListener('click', () => { box.querySelector('img').src = img.src; box.classList.add('on'); }));
  box.addEventListener('click', () => box.classList.remove('on'));
  addEventListener('keydown', e => { if (e.key === 'Escape') box.classList.remove('on'); });
}
