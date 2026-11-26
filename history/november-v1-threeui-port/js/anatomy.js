// V4.8: four authored leader lines, attached to the visible component surfaces.
// Scroll draws the line first, then reveals the name and its product argument.
const clamp = v => Math.max(0, Math.min(1, v));
const smooth = (v, a, b) => { const t = clamp((v-a)/(b-a)); return t*t*(3-2*t); };
export const ANATOMY_LAYERS = ['battery', 'thermal', 'computer', 'tray'];
export const ANATOMY_STARTS = [1.995, 2.050, 2.105, 2.160];
export function anatomyAt(t) {
  const exit = 1 - smooth(t, 2.22, 2.245);
  return ANATOMY_LAYERS.map((key, i) => {
    const start = ANATOMY_STARTS[i], next = ANATOMY_STARTS[i+1] ?? 10;
    const line = smooth(t, start, start+.018);
    const text = smooth(t, start+.018, start+.032);
    const detail = smooth(t, start+.024, start+.040);
    return {
      key, line, text, detail,
      alpha: exit * smooth(t, start, start+.003),
      compactAlpha: exit * (1-smooth(t, next-.010, next)),
      emphasis: 1, // ThreeUI polish: earlier callouts no longer dim (was 1-.35*smooth(t, next, next+.018))
      active: t >= start && t < next && t < 2.245,
      complete: t >= start+.040,
    };
  });
}
export function createAnatomy({ root, source, project }) {
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.classList.add('anatomy-leaders');
  svg.setAttribute('aria-hidden', 'true');
  root.replaceChildren(svg);
  root.setAttribute('aria-hidden', 'true');
  const entries = ANATOMY_LAYERS.map((key, i) => {
    const item = source.children[i];
    const group = document.createElementNS(ns, 'g');
    const path = document.createElementNS(ns, 'path');
    path.setAttribute('pathLength', '1');
    path.setAttribute('fill', 'none');
    const dot = document.createElementNS(ns, 'circle');
    dot.setAttribute('r', '3');
    const core = document.createElementNS(ns, 'circle');
    core.setAttribute('r', '1');
    core.classList.add('anatomy-core');
    group.append(path, dot, core);svg.append(group);
    const label = document.createElement('div');
    label.className = 'anatomy-label';
    label.dataset.layer = key;
    const number = document.createElement('p');number.className='anatomy-code';
    number.textContent = item.querySelector('span').textContent;
    const title = document.createElement('h3');title.textContent=item.querySelector('strong').textContent;
    const detail = document.createElement('p');detail.className='anatomy-note';
    detail.textContent=item.querySelector('p').textContent;
    label.append(number,title,detail);root.append(label);
    return { key, item, group, path, dot, core, label, title, detail };
  });
  let size = {w:0,h:0}, compact = false, metrics=[];
  function resize(w,h) {
    size={w,h};compact=w<1100||h<640||w/h<1.3;
    root.classList.toggle('is-compact',compact);
    svg.setAttribute('viewBox',`0 0 ${w} ${h}`);
  }
  function update(t) {
    const states=anatomyAt(t), visible=t>=ANATOMY_STARTS[0]&&t<2.245;
    root.style.opacity=visible?'1':'0';
    root.style.visibility=visible?'visible':'hidden';
    const {w,h}=size;
    // ThreeUI polish: wider labels, pulled in from the edge, more so below 1400px.
    const padding=Math.max(24,w*.055), width=compact?Math.min(440,w-2*padding):Math.min(350,w*.243);
    const x=compact?(w-width)/2:w-padding-width-23-(w<1400?48*Math.min(1,(1400-w)/120):0);
    metrics=states.map((s,i)=>{
      const e=entries[i];
      e.item.style.setProperty('--layer-progress',s.line);
      e.item.classList.toggle('is-current',s.active);
      e.item.classList.toggle('is-seen',s.complete);
      if(s.active)e.item.setAttribute('aria-current','step');else e.item.removeAttribute('aria-current');
      if(!visible)return {key:s.key,...s,visible:false};
      const point=project(e.key);
      const y=compact?h-232: h*.218+i*Math.min(h*.137,140);
      let path;
      if(compact){
        const lane=Math.min(w-12,Math.max(point.x+30,x+width+14));
        path=`M ${point.x} ${point.y} L ${lane} ${point.y} L ${lane} ${y} L ${x+width-14} ${y}`;
      }else{
        const endY=y+7,elbow=Math.min(x-22,point.x+Math.max(28,(x-point.x)*.48));
        path=`M ${point.x} ${point.y} L ${elbow} ${point.y} L ${x-22} ${endY} L ${x-10} ${endY}`;
      }
      e.path.setAttribute('d',path);
      e.path.style.strokeDashoffset=String(1-s.line);
      const alpha=compact?s.alpha*s.compactAlpha:s.alpha;
      e.group.style.opacity=String(alpha*s.emphasis);
      for(const dot of [e.dot,e.core]){dot.setAttribute('cx',point.x);dot.setAttribute('cy',point.y);}
      e.label.style.width=`${width}px`;
      e.label.style.transform=`translate3d(${x+8*(1-s.text)}px,${y}px,0)`;
      e.label.style.opacity=String(alpha*s.text*s.emphasis);
      e.detail.style.opacity=String(s.detail);
      e.label.classList.toggle('is-current',s.active);
      return {...s,visible:alpha*s.text>.01,point,box:{x,y,width},path,compact};
    });
  }
  return { resize,update,inspect:()=>({compact,size,samples:metrics}) };
}
