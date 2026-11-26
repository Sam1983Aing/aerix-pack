// The same scroll clock draws five leaders from the actual study surfaces.
import {smooth} from './story.js?v=4.12';
export const PERFORMANCE_PARTS = {
  radio:'FC30_RADIO_CAN',
  processor:'FC30_PROCESSOR_HEATCAP',
  imu:'FC30_IMU_PACKAGE',
  m2:'FC32_MEMORY_INDEX.001',
  m1:'FC32_MEMORY_INDEX',
};
export const PERFORMANCE_STARTS=[4.339,4.343,4.347,4.351,4.355];
export function performanceAt(t) {
  const exit=1-smooth(t,4.363,4.365);
  return Object.keys(PERFORMANCE_PARTS).map((key,i)=>{
    const start=PERFORMANCE_STARTS[i],next=PERFORMANCE_STARTS[i+1]??10;
    return {key,line:smooth(t,start,start+.0015),text:smooth(t,start+.0015,start+.003),
      alpha:exit*(1-.28*smooth(t,next,next+.0015)),
      compactAlpha:exit*(1-smooth(t,next-.001,next)),
      active:t>=start&&t<next&&t<4.365};
  });
}
export function createPerformance({root,source,project}) {
  const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');
  svg.classList.add('performance-leaders');
  const heading=document.createElement('div');heading.className='performance-heading';
  heading.innerHTML='<p class="mono">04 / THE FLIGHT COMPUTER</p><h3>Performance begins here.</h3>';
  root.replaceChildren(svg,heading);
  const entries=[...source.children].map((item,i)=>{
    const group=document.createElementNS(ns,'g'),path=document.createElementNS(ns,'path'),dot=document.createElementNS(ns,'circle');
    path.setAttribute('pathLength','1');dot.setAttribute('r','2.7');group.append(path,dot);svg.append(group);
    const label=document.createElement('div');label.className='performance-label';label.dataset.part=item.dataset.part;
    const code=document.createElement('p');code.className='performance-code mono';code.textContent=item.querySelector('span').textContent;
    const title=document.createElement('h3');title.textContent=item.querySelector('strong').textContent;
    const note=document.createElement('p');note.className='performance-note';note.textContent=item.querySelector('p').textContent;
    label.append(code,title,note);root.append(label);
    return {key:item.dataset.part,item,group,path,dot,label,i};
  });
  let w=0,h=0,compact=false,metrics=[];
  function resize(width,height){w=width;h=height;compact=w<1100||h<640||w/h<1.3;root.classList.toggle('is-compact',compact);svg.setAttribute('viewBox',`0 0 ${w} ${h}`);}
  function update(t){
    const visible=t>=4.337&&t<4.366;
    root.style.visibility=visible?'visible':'hidden';
    root.style.opacity=String(smooth(t,4.337,4.339)*(1-smooth(t,4.363,4.366)));
    const states=performanceAt(t),pad=Math.max(24,w*.05),width=compact?Math.min(440,w-pad*2):Math.min(255,w*.19);
    metrics=entries.map((e,i)=>{
      const state=states[i];e.item.setAttribute('aria-current',state.active?'step':'false');
      if(!visible)return {...state,visible:false};
      const left=i<3,x=compact?(w-width)/2:left?pad:w-pad-width;
      const y=compact?h-212:h*(left?[.29,.47,.65][i]:[.46,.65][i-3]);
      const point=project(e.key);
      let path;
      if(compact){
        const lane=w-14;
        path=`M ${point.x} ${point.y} L ${lane} ${point.y} L ${lane} ${y} L ${x+width-16} ${y}`;
      } else {
        const endX=left?x+width+10:x-10,endY=y+6;
        const elbow=left?Math.min(point.x-24,endX+48):Math.max(point.x+24,endX-48);
        path=`M ${point.x} ${point.y} L ${elbow} ${point.y} L ${endX+(left?14:-14)} ${endY} L ${endX} ${endY}`;
      }
      const alpha=compact?state.compactAlpha:state.alpha;
      e.path.setAttribute('d',path);e.path.style.strokeDashoffset=String(1-state.line);
      e.group.style.opacity=String(alpha*state.line);
      e.dot.setAttribute('cx',point.x);e.dot.setAttribute('cy',point.y);
      e.label.style.width=`${width}px`;e.label.style.transform=`translate3d(${x}px,${y+6*(1-state.text)}px,0)`;
      e.label.style.opacity=String(alpha*state.text);e.label.classList.toggle('is-current',state.active);
      return {...state,visible:alpha*state.text>.01,point,box:{x,y,width},path,compact};
    });
  }
  return {resize,update,inspect:()=>({compact,size:{w,h},samples:metrics})};
}
