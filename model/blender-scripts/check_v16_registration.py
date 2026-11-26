"""Compare the four board bores, PCB station and every aircraft track to V15."""
import sys,json
from pathlib import Path
import bpy
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from v16_reference import core_xy,pd_holes

def get_fit(version):
    bpy.context.window.scene=bpy.data.scenes[version+' · Assembled']
    pcb=bpy.data.objects['Board.core'];bpy.context.scene.frame_set(1)
    vs=[pcb.matrix_world@v.co*1000 for v in pcb.data.vertices]
    bounds=[(min(p[i] for p in vs),max(p[i] for p in vs)) for i in range(3)]
    holes=[]
    for uv in pd_holes:
        x,y=core_xy(*uv)
        pts=[tuple(round(float(c),5) for c in p) for p in vs if abs(((p.x-x)**2+(p.y-y)**2)**.5-.82)<.0001]
        assert len(set(pts))>=48,(uv,len(set(pts)))
        holes.append(sorted(set(pts)))
    group=bpy.data.collections[version+' | Aircraft'];poses=[]
    for frame in range(1,122):
        bpy.context.scene.frame_set(frame)
        poses.append({o.name:tuple(float(value) for row in o.matrix_world for value in row) for o in group.objects if o.type=='MESH'})
    return bounds,holes,poses

assert Path(bpy.data.filepath).name=='drone-v16.blend'
current=get_fit('V16')
bpy.ops.wm.open_mainfile(filepath=str(root/'blender/drone-v15.blend'))
approved=get_fit('V15')
assert all(abs(x-y)<.0001 for a,b in zip(current[0],approved[0]) for x,y in zip(a,b))
assert current[1]==approved[1]
assert current[2]==approved[2]
report={'datum':'V15 world millimetres','board_bounds_xyz_mm':current[0],
 'unchanged_mounting_bores':4,'registered_bore_vertices':sum(map(len,current[1])),
 'aircraft_mesh_tracks_compared_to_V15':len(current[2][0]),'identical_pose_frames':len(current[2])}
(root/'measurements/v16-registration.json').write_text(json.dumps(report,indent=2)+'\n')
print('V15 REGISTRATION',report)

