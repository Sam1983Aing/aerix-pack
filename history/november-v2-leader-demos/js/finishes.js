// Color changes apply only to the two upper-shell materials. All texture maps,
// roughness, metalness, normals, decals and the black chassis remain original.
export const FINISHES=Object.freeze([
  {id:'titanium-blue',name:'Titanium Blue',color:'#819db5',swatch:'#9db9ce'},
  {id:'obsidian-metal',name:'Obsidian Metal',color:'#4b545f',swatch:'#505b68'},
  {id:'tactical-green',name:'Tactical Green',color:'#737c60',swatch:'#7e896e'},
  {id:'crimson-alloy',name:'Crimson Alloy',color:'#90484d',swatch:'#a65c62'},
  {id:'glacial-titanium',name:'Pearl Silver',original:true,swatch:'#c4c6c5'},
]);
export const DEFAULT_FINISH=FINISHES.find(f=>f.id==='titanium-blue');
export const CONCEPT_PRICE={amount:2499,currency:'USD',label:'$2,499 USD'};
