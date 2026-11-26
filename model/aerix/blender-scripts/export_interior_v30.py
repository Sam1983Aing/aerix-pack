"""Swap the three interior layers in V29's exact GLB data, with baked textures and staged reveal."""
import json,struct,copy,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'renders/interior-v30';c=json.loads((O/'integration-config.json').read_text())
def read(p):
 b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);k=20+n;l=struct.unpack_from('<I',b,k)[0];return j,b[k+8:k+8+l]
g,original=read(R/'exports/aerix-review-v29.glb');a,extra=read(R/'exports/aerix-interior-additions-v30.glb');data=bytearray(original)
counts={k:len(g.get(k,[])) for k in ['meshes','materials','nodes','accessors','bufferViews','images','textures','samplers']};originalmeshes=copy.deepcopy(g['meshes']);originalmats=copy.deepcopy(g['materials']);oldclips={x['name']:copy.deepcopy(x) for x in g['animations']}
while len(data)%4:data.append(0)
offset=len(data);data.extend(extra)
for v in a['bufferViews']:
 v=copy.deepcopy(v);v['byteOffset']=v.get('byteOffset',0)+offset;g['bufferViews'].append(v)
for v in a['accessors']:
 v=copy.deepcopy(v);v['bufferView']+=counts['bufferViews'];g['accessors'].append(v)
for im in a.get('images',[]):
 im=copy.deepcopy(im)
 if 'bufferView' in im:im['bufferView']+=counts['bufferViews']
 g.setdefault('images',[]).append(im)
g.setdefault('samplers',[]).extend(a.get('samplers',[]))
for tex in a.get('textures',[]):
 tex=copy.deepcopy(tex)
 if 'source' in tex:tex['source']+=counts['images']
 if 'sampler' in tex:tex['sampler']+=counts['samplers']
 g.setdefault('textures',[]).append(tex)
def textures(obj):
 if isinstance(obj,dict):
  for k,v in obj.items():
   if k.lower().endswith('texture') and isinstance(v,dict) and 'index' in v:v['index']+=counts['textures']
   else:textures(v)
 elif isinstance(obj,list):
  for v in obj:textures(v)
for m in a['materials']:m=copy.deepcopy(m);textures(m);g['materials'].append(m)
for mesh in a['meshes']:
 mesh=copy.deepcopy(mesh)
 for p in mesh['primitives']:
  p['attributes']={k:v+counts['accessors'] for k,v in p['attributes'].items()}
  if 'indices' in p:p['indices']+=counts['accessors']
  if 'material' in p:p['material']+=counts['materials']
 g['meshes'].append(mesh)
names={n.get('name'):i for i,n in enumerate(g['nodes'])};parents={ch:i for i,n in enumerate(g['nodes']) for ch in n.get('children',[])}
# Detach obsolete layer geometry; preserve its original binary records as historical data.
for name in c['old_parts']:
 if name not in names:continue
 i=names[name];pi=parents.get(i)
 if pi is not None:g['nodes'][pi]['children'].remove(i)
 for sc in g['scenes']:
  if i in sc.get('nodes',[]):sc['nodes'].remove(i)
C=[[1,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1]];CI=[list(x) for x in zip(*C)]
def mm(a,b):return [[sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
def local(node,raw):
 m=mm(mm(C,[raw[i:i+4] for i in range(0,16,4)]),CI)
 for k in ['matrix','translation','rotation','scale']:node.pop(k,None)
 if all(abs(m[i][j]-(1 if i==j else 0))<1e-6 for i in range(3) for j in range(3)):node['translation']=[m[i][3] for i in range(3)]
 else:node['matrix']=[m[i][j] for j in range(4) for i in range(4)]
needed=set(c['new_mesh_names'])|set(c['tracks']);meshnodes={n['name']:n for n in a['nodes'] if 'mesh' in n}
assert set(c['new_mesh_names'])<=set(meshnodes),set(c['new_mesh_names'])-set(meshnodes)
for name in list(needed):
 p=c['hierarchy'][name]['parent']
 while p and p not in names:needed.add(p);p=c['hierarchy'][p]['parent']
for name in sorted(needed):
 if name in names:continue
 node={'name':name}
 if name in meshnodes:node['mesh']=meshnodes[name]['mesh']+counts['meshes']
 local(node,c['hierarchy'][name]['local_matrix']);names[name]=len(g['nodes']);g['nodes'].append(node)
for name in needed:
 i=names[name];p=c['hierarchy'][name]['parent'];pi=names.get(p)
 if pi is None:continue
 if parents.get(i)!=pi:
  old=parents.get(i)
  if old is not None and i in g['nodes'][old].get('children',[]):g['nodes'][old]['children'].remove(i)
  g['nodes'][pi].setdefault('children',[]).append(i);parents[i]=pi;local(g['nodes'][i],c['hierarchy'][name]['local_matrix'])
def acc(vals,kind,count,lo=None,hi=None):
 while len(data)%4:data.append(0)
 start=len(data);data.extend(struct.pack('<'+'f'*len(vals),*vals));vi=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':len(data)-start});idx=len(g['accessors']);v={'bufferView':vi,'componentType':5126,'count':count,'type':kind}
 if lo is not None:v['min']=lo;v['max']=hi
 g['accessors'].append(v);return idx
times=[k/30 for k in range(121)];tid=acc(times,'SCALAR',121,[0],[4])
for clip in ['Thermal_detail','Computer_detail','Tray_detail']:
 anim={'name':clip,'samplers':[],'channels':[]}
 for name,track in c['tracks'].items():
  if track['clip']!=clip:continue
  vals=[v for p in track['samples'] for v in [p[0],p[2],-p[1]]];ai=acc(vals,'VEC3',121);si=len(anim['samplers']);anim['samplers'].append({'input':tid,'output':ai,'interpolation':'LINEAR'});anim['channels'].append({'sampler':si,'target':{'node':names[name],'path':'translation'}})
 g['animations'].append(anim)
g['extensionsUsed']=list(dict.fromkeys(g.get('extensionsUsed',[])+a.get('extensionsUsed',[])));g['buffers'][0]['byteLength']=len(data)
g['asset'].setdefault('extras',{})['interiorStudy']='V30 refined thermal cover, flight computer and support tray. V29 battery and original four clips retained.'
encoded=json.dumps(g,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4);data+=b'\0'*((-len(data))%4);dest=R/'exports/aerix-review-v30.glb';dest.write_bytes(struct.pack('<III',0x46546c67,2,28+len(encoded)+len(data))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(data),0x004e4942)+data)
active=set()
def visit(i):
 if i in active:return
 active.add(i)
 for ch in g['nodes'][i].get('children',[]):visit(ch)
for sc in g['scenes']:
 for i in sc.get('nodes',[]):visit(i)
checks={'original_binary_preserved':bytes(data[:len(original)])==original,'old_mesh_records_unchanged':g['meshes'][:counts['meshes']]==originalmeshes,'old_material_records_unchanged':g['materials'][:counts['materials']]==originalmats,'all_four_original_clips_preserved':all(x==oldclips[x['name']] for x in g['animations'] if x['name'] in oldclips),'old_layers_detached':all(names[n] not in active for n in c['old_parts'] if n in names),'new_layers_attached':all(names[n] in active for n in c['new_mesh_names'])};assert all(checks.values()),checks
(O/'export-validation.json').write_text(json.dumps({'checks':checks,'bytes':dest.stat().st_size,'active_mesh_nodes':sum('mesh' in g['nodes'][i] for i in active),'new_mesh_nodes':len(c['new_mesh_names']),'embedded_images':len(g['images']),'new_images':len(a.get('images',[])),'animations':[x['name'] for x in g['animations']]},indent=2));print('V30_MERGED_EXPORT',checks,flush=True)
