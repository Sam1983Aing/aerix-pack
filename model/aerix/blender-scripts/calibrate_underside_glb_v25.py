"""Keep contact shading subtle on narrow underside fillets in the inspection GLB."""
import copy,json,struct
from pathlib import Path
R=Path(__file__).resolve().parents[2]
TARGETS={'BELLY_VENT_TUNNEL_-1','BELLY_VENT_TUNNEL_1'}
def calibrate(path):
 data=path.read_bytes();size,kind=struct.unpack_from('<II',data,12);g=json.loads(data[20:20+size]);remaining=data[20+size:]
 label='V25 underside trim contact shading';idx=next((i for i,m in enumerate(g['materials']) if m.get('name')==label),None);count=0
 for node in g['nodes']:
  if node.get('name') not in TARGETS or 'mesh' not in node:continue
  for primitive in g['meshes'][node['mesh']]['primitives']:
   material=g['materials'][primitive['material']]
   if 'occlusionTexture' not in material:continue
   if idx is None:
    calibrated=copy.deepcopy(material);calibrated['name']=label;calibrated['occlusionTexture']['strength']=.45;idx=len(g['materials']);g['materials'].append(calibrated)
   primitive['material']=idx;count+=1
 assert count==len(TARGETS),(count,TARGETS)
 g['materials'][idx]['occlusionTexture']['strength']=.45
 raw=json.dumps(g,separators=(',',':')).encode();raw+=b' '*((-len(raw))%4);length=12+8+len(raw)+len(remaining)
 path.write_bytes(struct.pack('<III',0x46546c67,2,length)+struct.pack('<II',len(raw),kind)+raw+remaining)
 print('V25_UNDERSIDE_CONTACT_SHADING',count,flush=True)
if __name__=='__main__':calibrate(R/'exports/aerix-review-v25.glb')
