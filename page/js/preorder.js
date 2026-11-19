import {FINISHES,DEFAULT_FINISH,CONCEPT_PRICE} from './finishes.js?v=4.16.1';

export function createPreorder({onFinish,onOpen,onClose}) {
  const dialog=document.querySelector('#preorder'),status=document.querySelector('#preorder-status');
  let selected=DEFAULT_FINISH,opener;
  // A local concept configuration, never an order or a payment submission.
  try{const saved=JSON.parse(localStorage.getItem('aerix-configuration-v1')||'null');selected=FINISHES.find(f=>f.id===saved?.finish)||selected;}catch{}
  const groups=[...document.querySelectorAll('[data-finish-options]')];
  groups.forEach((group,i)=>{
    for(const finish of FINISHES){
      const label=document.createElement('label');label.className='finish-option';
      const input=document.createElement('input');input.type='radio';input.name=`finish-${i}`;input.value=finish.id;input.setAttribute('aria-label',finish.name);
      const chip=document.createElement('span');chip.className='finish-swatch';chip.style.setProperty('--finish',finish.swatch);chip.setAttribute('aria-hidden','true');
      const text=document.createElement('span');text.className='finish-option-name';text.textContent=finish.name;
      label.append(input,chip,text);group.append(label);
      input.addEventListener('change',()=>select(finish.id));
    }
  });
  function select(id){
    selected=FINISHES.find(f=>f.id===id)||DEFAULT_FINISH;
    document.querySelectorAll('[data-finish-name]').forEach(n=>n.textContent=selected.name);
    document.querySelectorAll('[data-finish-price]').forEach(n=>n.textContent=CONCEPT_PRICE.label);
    groups.forEach(g=>g.querySelectorAll('input').forEach(n=>n.checked=n.value===selected.id));
    status.textContent='';document.querySelector('#save-configuration').textContent='Save my configuration';
    onFinish(selected.id);
  }
  function close(){if(!dialog.open)return;dialog.close();onClose();opener?.focus({preventScroll:true});}
  document.querySelectorAll('[data-preorder]').forEach(button=>button.addEventListener('click',()=>{
    opener=button;status.textContent='';document.querySelector('#save-configuration').textContent='Save my configuration';dialog.showModal();onOpen();
  }));
  document.querySelector('#close-preorder').addEventListener('click',close);
  dialog.addEventListener('cancel',e=>{e.preventDefault();close();});
  dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)close();}});
  document.querySelector('#preorder-form').addEventListener('submit',e=>{
    e.preventDefault();
    try{
      localStorage.setItem('aerix-configuration-v1',JSON.stringify({finish:selected.id,price:CONCEPT_PRICE.amount,currency:CONCEPT_PRICE.currency}));
      status.textContent=`${selected.name} saved on this device. No order has been placed.`;
      document.querySelector('#save-configuration').textContent='Configuration saved ✓';
    }catch{status.textContent='Your selection is ready. This browser could not save it on this device.';}
  });
  select(selected.id);
  return {get selected(){return selected;},get open(){return dialog.open;}};
}
