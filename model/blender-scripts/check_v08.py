"""Evaluate mesh connectivity and record contacts throughout the complete fold."""
from pathlib import Path
import sys, json, bpy
from itertools import combinations
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_v04_assembly import audit,local_meshes,world_solids,widths
export='--export' in sys.argv
if export:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps=30
    bpy.ops.import_scene.gltf(filepath=str(ROOT/'exports/drone-v08.glb'))
    group=bpy.context.scene.collection
    class Imported:
        objects=[o for o in group.all_objects]
    group=Imported()
else:
    group=bpy.data.collections['V08 | Aircraft']
scene=bpy.context.scene
scene.frame_set(1)
rows=audit(group,range(1,122))
base=set(map(tuple,rows[0]['contacts']))
changes={}
disconnected={}
for row in rows:
    if len(row['groups'])>1: disconnected[row['frame']]=row['groups'][1:]
    for pair in set(map(tuple,row['contacts']))-base:
        changes.setdefault(' / '.join(pair),[]).append(row['frame'])
solids=world_solids(local_meshes(group),{})
airframe=[s for name,s in solids.items() if not name.startswith('Propeller.blade.')]
naked=[round(1000*(max(s.hi[i] for s in airframe)-min(s.lo[i] for s in airframe)),2) for i in (1,0,2)]
hubs={code:bpy.data.objects['Propeller.hub.'+code].matrix_world.translation*1000 for code in ('FR','FL','RR','RL')}
motor_diag=(hubs['FL']-hubs['RR']).to_2d().length
fixed_contacts=sorted(' / '.join(pair) for pair in base if any(n.startswith(('Arm.','Leg.front.','Propeller.blade.','Hinge.pin.')) for n in pair))
result={'frames':len(rows),'mesh_count':len(solids),'open_mm':rows[0]['size_mm'],'folded_mm':rows[-1]['size_mm'],
        'open_without_propellers_mm':naked,'diagonal_mm':round(motor_diag,3),'shell_sections_mm':widths(group),
        'new_contacts':changes,'disconnected_frames':disconnected,'open_moving_contacts':fixed_contacts}
tag='export' if export else 'native'
(ROOT/f'measurements/v08-{tag}-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print({k:v for k,v in result.items() if k not in ('new_contacts','disconnected_frames','open_moving_contacts')})
for pair,frames in changes.items(): print(pair,frames[0],frames[-1])
print('Disconnected:',len(disconnected),list(disconnected.items())[:1])
print('Open moving contacts:',fixed_contacts)
