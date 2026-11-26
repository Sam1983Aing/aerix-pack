import { createPin, placePin } from './part-pins.js';
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
      alpha:exit, // ThreeUI polish: earlier labels no longer dim (was exit*(1-.28*smooth(t,next,next+.0015)))
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
  const LABEL_ROWS=[.275,.458,.658,.378,.6], layout={w:-1,h:-1,on:false,top:[]};
  // Round 2: Numbered Pins replace the leader lines (see part-pins.js).
  const pins=entries.map((e,i)=>createPin(svg,String(i+1).padStart(2,'0')));
  function resize(width,height){w=width;h=height;compact=w<1100||h<640||w/h<1.3;root.classList.toggle('is-compact',compact);svg.setAttribute('viewBox',`0 0 ${w} ${h}`);}
  function update(t){
    const visible=t>=4.337&&t<4.366;
    root.style.visibility=visible?'visible':'hidden';
    root.style.opacity=String(smooth(t,4.337,4.339)*(1-smooth(t,4.363,4.366)));
    const states=performanceAt(t),pad=Math.max(24,w*.05),width=compact?Math.min(440,w-pad*2):Math.min(336,w*.233);
    // ThreeUI polish: wider labels, and each label's top is measured so a longer note
    // pushes the next one down instead of overlapping it. Re-measured only on resize.
    const shift=!compact&&w<1400?48*Math.min(1,(1400-w)/120):0;
    if(!compact&&visible&&(!layout.on||width!==layout.w||h!==layout.h)){
      const heights=entries.map(e=>(e.label.style.width=`${width}px`,e.label.offsetHeight));
      layout.top=LABEL_ROWS.map(row=>h*row);
      [1,2,4].forEach(i=>layout.top[i]=Math.max(layout.top[i],layout.top[i-1]+heights[i-1]+22));
      layout.w=width;layout.h=h;
    }
    layout.on=visible;
    metrics=entries.map((e,i)=>{
      if(!visible)pins[i].style.opacity='0';
      const state=states[i];e.item.setAttribute('aria-current',state.active?'step':'false');
      if(!visible)return {...state,visible:false};
      const left=i<3,x=compact?(w-width)/2:left?pad:w-pad-width-20-shift;
      const y=compact?h-212:layout.top[i]??h*LABEL_ROWS[i];
      const point=project(e.key);
      let path;
      if(compact){
        const lane=w-14;
        path=`M ${point.x} ${point.y} L ${lane} ${point.y} L ${lane} ${y} L ${x+width-16} ${y}`;
      } else {
        const endX=left?x+width+10:x-10,endY=y+6;
        const elbow=left?Math.min(point.x-24,endX+48):Math.max(point.x+24,endX-48);
        // ThreeUI polish: right-hand leaders run straight to their label, without the elbow.
        path=left
          ?`M ${point.x} ${point.y} L ${elbow} ${point.y} L ${endX+14} ${endY} L ${endX} ${endY}`
          :`M ${point.x} ${point.y} L ${endX-14} ${endY} L ${endX} ${endY}`;
      }
      const alpha=compact?state.compactAlpha:state.alpha;
      e.path.setAttribute('d',path);e.path.style.strokeDashoffset=String(1-state.line);
      e.group.style.opacity=String(alpha*state.line);
      e.dot.setAttribute('cx',point.x);e.dot.setAttribute('cy',point.y);
      e.label.style.width=`${width}px`;e.label.style.transform=`translate3d(${x}px,${y+6*(1-state.text)}px,0)`;
      e.label.style.opacity=String(alpha*state.text);e.label.classList.toggle('is-current',state.active);
      placePin(pins[i],point,alpha*state.text,state.active);
      return {...state,visible:alpha*state.text>.01,point,box:{x,y,width},path,compact};
    });
  }
  return {resize,update,inspect:()=>({compact,size:{w,h},samples:metrics})};
}
