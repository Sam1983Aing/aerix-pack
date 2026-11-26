"""Retain the exact V27 meshes/textures/fold clip, append interior meshes and reveal tracks."""
import json,struct,copy,math,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'renders/interior-v28';c=json.loads((O/'integration-config.json').read_text())
def read(p):
 b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);k=20+n;l=struct.unpack_from('<I',b,k)[0];return j,b[k+8:k+8+l]
g,original=read(R/'exports/aerix-review-v27.glb');a,extra=read(R/'exports/aerix-interior-additions-v28.glb');data=bytearray(original)
counts={k:len(g.get(k,[])) for k in ['meshes','materials','nodes','accessors','bufferViews','images','textures','samplers']};original_meshes=copy.deepcopy(g['meshes']);original_mats=copy.deepcopy(g['materials']);fold=copy.deepcopy(g['animations'][0])
while len(data)%4:data.append(0)
offset=len(data);data.extend(extra)
for v in a['bufferViews']:
 v=copy.deepcopy(v);v['byteOffset']=v.get('byteOffset',0)+offset;g['bufferViews'].append(v)
for v in a['accessors']:
 v=copy.deepcopy(v);v['bufferView']+=counts['bufferViews'];g['accessors'].append(v)
g['materials'].extend(a['materials'])
for m in a['meshes']:
 m=copy.deepcopy(m)
 for p in m['primitives']:
  p['attributes']={k:v+counts['accessors'] for k,v in p['attributes'].items()}
  if 'indices' in p:p['indices']+=counts['accessors']
  if 'material' in p:p['material']+=counts['materials']
 g['meshes'].append(m)
names={n.get('name'):i for i,n in enumerate(g['nodes'])};parents={ch:i for i,n in enumerate(g['nodes']) for ch in n.get('children',[])}
# glTF conversion of Blender local matrices, without touching any geometry or material record.
C=[[1,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1]];CI=[list(x) for x in zip(*C)]
def mm(a,b):return [[sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
def setlocal(node,raw):
 m=[raw[i:i+4] for i in range(0,16,4)];v=mm(mm(C,m),CI)
 # All newly authored reveal roots are pure translations. Matrices on animated nodes are invalid glTF.
 identity=all(abs(v[i][j]-(1 if i==j else 0))<1e-6 for i in range(3) for j in range(3))
 for k in ['matrix','translation','rotation','scale']:node.pop(k,None)
 if identity:node['translation']=[v[i][3] for i in range(3)]
 else:node['matrix']=[v[i][j] for j in range(4) for i in range(4)]
needed=set(c['new_mesh_names'])|set(c['tracks'])
for name in list(needed):
 p=c['hierarchy'][name]['parent']
 while p and p not in names:
  needed.add(p);p=c['hierarchy'][p]['parent']
meshnodes={n['name']:n for n in a['nodes'] if 'mesh' in n}
for name in sorted(needed):
 if name in names:continue
 node={'name':name}
 if name in meshnodes:node['mesh']=meshnodes[name]['mesh']+counts['meshes']
 names[name]=len(g['nodes']);g['nodes'].append(node);setlocal(node,c['hierarchy'][name]['local_matrix'])
# Update only changed parentage from the native master; leave all folding transforms exact.
for name,i in list(names.items()):
 if name not in c['hierarchy']:continue
 parent=c['hierarchy'][name]['parent'];pi=names.get(parent)
 if pi is None:continue
 old=parents.get(i)
 if old!=pi:
  if old is not None:g['nodes'][old]['children'].remove(i)
  g['nodes'][pi].setdefault('children',[]).append(i);parents[i]=pi
  setlocal(g['nodes'][i],c['hierarchy'][name]['local_matrix'])
def acc(values,kind,count,lo=None,hi=None):
 while len(data)%4:data.append(0)
 start=len(data);data.extend(struct.pack('<'+'f'*len(values),*values));vi=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':len(data)-start});ai=len(g['accessors']);v={'bufferView':vi,'componentType':5126,'count':count,'type':kind}
 if lo is not None:v['min']=lo;v['max']=hi
 g['accessors'].append(v);return ai
for clip in ['Body_reveal','Battery_reveal','Optics_reveal']:
 anim={'name':clip,'samplers':[],'channels':[]};times=[i/30 for i in range(121)];tid=acc(times,'SCALAR',121,[0],[4])
 for name,t in c['tracks'].items():
  if t['clip']!=clip:continue
  base=t['base'];delta=t['offset'];vals=[]
  for k in range(121):
   u=k/120;u=u*u*(3-2*u);p=[base[i]+delta[i]*u for i in range(3)];vals.extend([p[0],p[2],-p[1]])
  aid=acc(vals,'VEC3',121);si=len(anim['samplers']);anim['samplers'].append({'input':tid,'output':aid,'interpolation':'LINEAR'});anim['channels'].append({'sampler':si,'target':{'node':names[name],'path':'translation'}})
 g['animations'].append(anim)
g['extensionsUsed']=list(dict.fromkeys(g.get('extensionsUsed',[])+a.get('extensionsUsed',[])));g['buffers'][0]['byteLength']=len(data)
g['asset'].setdefault('extras',{})['interiorStudy']='V28 fitted interior; unchanged V27 exterior mesh/material bytes. Independent body, battery and optics reveals.'
encoded=json.dumps(g,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4);data+=b'\0'*((-len(data))%4);dest=R/'exports/aerix-review-v28.glb'
dest.write_bytes(struct.pack('<III',0x46546c67,2,28+len(encoded)+len(data))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(data),0x004e4942)+data)
checks={'all_original_binary_bytes_retained':bytes(data[:len(original)])==original,'all_690_original_mesh_records_unchanged':g['meshes'][:counts['meshes']]==original_meshes,'all_49_original_material_records_unchanged':g['materials'][:counts['materials']]==original_mats,'fold_clip_unchanged':g['animations'][0]==fold,'four_independent_animations':len(g['animations'])==4}
assert all(checks.values());(O/'export-validation.json').write_text(json.dumps({'checks':checks,'bytes':dest.stat().st_size,'meshes':len(g['meshes']),'materials':len(g['materials']),'images':len(g['images']),'animations':[v['name'] for v in g['animations']]},indent=2));print('V28_EXPORT',checks)
