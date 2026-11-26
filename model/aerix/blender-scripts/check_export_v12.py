"""Check embedded assets and the fixed/moving arm hierarchy in the review GLB."""
from pathlib import Path
import struct,json
ROOT=Path(__file__).resolve().parents[2];p=ROOT/'exports/aerix-review-v12.glb';data=p.read_bytes()
magic,version,length=struct.unpack_from('<III',data);chunk,kind=struct.unpack_from('<II',data,12);g=json.loads(data[20:20+chunk]);names={n.get('name'):i for i,n in enumerate(g['nodes'])};parents={c:i for i,n in enumerate(g['nodes']) for c in n.get('children',[])}
fixed=[];moving=[];rotors=[]
for tag in ['FL','FR','RL','RR']:
 fixed.append(parents[names['HINGE_CHASSIS_MOUNT_'+tag]]==names['DRONE_ROOT'])
 for part in ['ARM_','ARM_INLAY_','HINGE_ROTATING_COLLAR_','HINGE_CAP_']:moving.append(parents[names[part+tag]]==names['ARM_'+tag+'_ROOT'])
 rotors.append(parents[names['PROPELLER_'+tag]]==names['ARM_'+tag+'_ROOT'])
checks={'valid_glb_header':magic==0x46546c67 and version==2 and length==len(data),'all_images_embedded':all('bufferView' in x and 'uri' not in x for x in g.get('images',[])),'no_external_buffers':all('uri' not in x for x in g.get('buffers',[])),'four_fixed_mounts':all(fixed),'arm_beams_collars_and_caps_parented_to_pivots':all(moving),'four_rotor_roots_retained':all(rotors),'eight_blades':sum(n.startswith('BLADE_') for n in names if n)==8,'graphite_ambient_occlusion_exported':any('molded graphite' in m.get('name','') and 'occlusionTexture' in m for m in g['materials'])}
report={'checks':checks,'bytes':len(data),'meshes':len(g.get('meshes',[])),'images':len(g.get('images',[])),'materials':len(g.get('materials',[]))};(ROOT/'renders/exterior-v12/export-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));assert all(checks.values())
