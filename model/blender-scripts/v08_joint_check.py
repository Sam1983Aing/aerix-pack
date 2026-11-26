"""Check triangle surface intersections of the rotating arms with their fixed housing."""
import bpy,sys,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from check_v04_assembly import local_meshes,world_solids
group=bpy.data.collections['V08 | Aircraft']
names={'Shell.moulded_fuselage'}|{'Arm.'+code for code in ('FR','FL','RR','RL')}
meshes={n:m for n,m in local_meshes(group).items() if n in names}
cache={}
hits=[]
for frame in range(1,122):
    bpy.context.scene.frame_set(frame)
    solids=world_solids(meshes,cache)
    hull=solids['Shell.moulded_fuselage']
    for name,a in solids.items():
        if name.startswith('Arm.') and a.contacts(hull): hits.append([frame,name])
print('Cuff intersections:',hits)
(root/'measurements/v08-cuff-check.json').write_text(json.dumps({'frames':121,'contacts':hits},indent=2)+'\n')
bpy.context.scene.frame_set(1)
