"""Extend V25's exact baked GLB with fold pivots and animation only."""
import json,struct,math,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];out=R/'renders/folding-v27'
config=json.loads((out/'fold-animation.json').read_text())
source=R/config['source'];raw=source.read_bytes();source_hash=hashlib.sha256(raw).hexdigest()
json_size=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+json_size])
bin_start=20+json_size;bin_size=struct.unpack_from('<I',raw,bin_start)[0];original_bin=raw[bin_start+8:bin_start+8+bin_size];data=bytearray(original_bin)
original_mesh_count=len(g['meshes']);original_material_count=len(g['materials']);original_meshes=json.dumps(g['meshes'],sort_keys=True);original_materials=json.dumps(g['materials'],sort_keys=True)
names={n.get('name'):i for i,n in enumerate(g['nodes'])}
for tag,p in config['pitch_pivots'].items():
 pivot=[p[0],p[2],-p[1]];root=g['nodes'][names['ARM_'+tag+'_ROOT']]
 children=[names[n] for n in config['pitch_children'][tag] if n in names]
 for child in children:
  node=g['nodes'][child]
  if 'matrix' in node:
   for i in range(3):node['matrix'][12+i]-=pivot[i]
  else:node['translation']=[a-b for a,b in zip(node.get('translation',[0.,0.,0.]),pivot)]
 name='ARM_'+tag+'_FOLD_PITCH';helper=len(g['nodes']);names[name]=helper
 g['nodes'].append({'name':name,'translation':pivot,'children':children})
 root['children']=[i for i in root['children'] if i not in children]+[helper]
for tag in ['FL','FR','RL','RR']:
 prop=g['nodes'][names['PROPELLER_'+tag]]
 for k in [0,1]:
  blade_id=names[f'BLADE_{tag}_{k}'];blade=g['nodes'][blade_id];pivot=(1 if k==0 else -1)*.01
  assert 'matrix' not in blade
  location=blade.get('translation',[0.,0.,0.]).copy();location[0]-=pivot;blade['translation']=location
  name=f'BLADE_FOLD_{tag}_{k}';helper=len(g['nodes']);names[name]=helper
  g['nodes'].append({'name':name,'translation':[pivot,0.,0.],'children':[blade_id]})
  prop['children']=[helper if i==blade_id else i for i in prop['children']]
def accessor(values,kind,count,minimum=None,maximum=None):
 while len(data)%4:data.append(0)
 offset=len(data);packed=struct.pack('<'+'f'*len(values),*values);data.extend(packed)
 view=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(packed)})
 idx=len(g['accessors']);a={'bufferView':view,'componentType':5126,'count':count,'type':kind}
 if minimum is not None:a['min']=minimum;a['max']=maximum
 g['accessors'].append(a);return idx
# New rear hinge hardware uses explicit satin materials; the V25 records stay intact.
material_ids={m['name']:i for i,m in enumerate(g['materials'])}
for detail in config.get('hinge_details',[]):
 material=detail['material'];label=material['name']
 if label not in material_ids:
  material_ids[label]=len(g['materials']);g['materials'].append(material)
 positions=detail['positions'];count=len(positions)//3
 low=[min(positions[i::3]) for i in range(3)];high=[max(positions[i::3]) for i in range(3)]
 position=accessor(positions,'VEC3',count,low,high);normal=accessor(detail['normals'],'VEC3',count)
 mesh_id=len(g['meshes']);g['meshes'].append({'name':detail['name'],'primitives':[{'attributes':{'POSITION':position,'NORMAL':normal},'material':material_ids[label]}]})
 node_id=len(g['nodes']);g['nodes'].append({'name':detail['name'],'mesh':mesh_id})
 g['nodes'][names[detail['parent']]].setdefault('children',[]).append(node_id)
times=[i/config['fps'] for i in range(config['samples'])]
time_id=accessor(times,'SCALAR',len(times),[0.],[config['duration']]);animation={'name':'Fold_arms_and_blades','samplers':[],'channels':[]}
for name,angles in config['tracks'].items():
 # Quaternions are authored in Blender and converted to glTF coordinates by the rig builder.
 values=[v for q in angles for v in q]
 value_id=accessor(values,'VEC4',len(angles));sampler=len(animation['samplers'])
 animation['samplers'].append({'input':time_id,'output':value_id,'interpolation':'LINEAR'})
 animation['channels'].append({'sampler':sampler,'target':{'node':names[name],'path':'rotation'}})
g['animations']=[animation];g['buffers'][0]['byteLength']=len(data)
g.setdefault('asset',{}).setdefault('extras',{})['foldingStudy']='V27 inward folding: reversed front blade fans and rear arms lowered beneath the front pair; V25 mesh and material data retained.'
encoded=json.dumps(g,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4);data+=b'\0'*((-len(data))%4)
output=struct.pack('<III',0x46546c67,2,28+len(encoded)+len(data))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(data),0x004e4942)+data
dest=R/'exports/aerix-review-v27.glb';dest.write_bytes(output)
checks={'original_binary_data_preserved':bytes(data[:len(original_bin)])==original_bin,'mesh_definitions_preserved':json.dumps(g['meshes'][:original_mesh_count],sort_keys=True)==original_meshes,'material_definitions_preserved':json.dumps(g['materials'][:original_material_count],sort_keys=True)==original_materials,'source_unchanged':hashlib.sha256(source.read_bytes()).hexdigest()==source_hash,'eighteen_rotation_tracks':len(animation['channels'])==18}
assert all(checks.values())
(out/'export-validation.json').write_text(json.dumps({'checks':checks,'source_sha256':source_hash,'bytes':len(output),'meshes':len(g['meshes']),'materials':len(g['materials']),'images':len(g['images']),'duration':config['duration']},indent=2))
print('V27_FOLD_EXPORT_COMPLETE',checks)
