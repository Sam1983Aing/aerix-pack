"""Measure the reference solid intersections and shoulder shape in the V12 scene."""
import sys
from pathlib import Path
import bpy
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from check_v04_assembly import local_meshes,world_solids
grp=bpy.data.collections['V12 | Aircraft']
bpy.context.scene.frame_set(1)
solids=world_solids(local_meshes(grp),{})
for name in ('Camera.block','Camera.face_trim','Gimbal.pitch_cover.R','Gimbal.trunnion.R','Gimbal.yoke.R','Hinge.socket.FR','Hinge.bracket.FR','Hinge.pin.FR','Arm.FR'):
    s=solids[name]
    print(name,'bounds mm',*[tuple(round(n*1000,2) for n in row) for row in [s.lo,s.hi]],'contacts',[k for k,o in solids.items() if k!=name and s.contacts(o)])
    obj=grp.objects[name]
    print('origin',tuple(round(n*1000,2) for n in obj.matrix_world.translation),
          'materials',[m.name for m in obj.data.materials])
shell=solids['Shell.moulded_fuselage'].tree
for y in [8,11,13,15,17,19,22]:
    row=[]
    for z in [28,29,30,31,32,33,34,35,36,37,38,40,42,44,46,48]:
        hit,*_=shell.ray_cast(Vector((.09,y*.001,z*.001)),Vector((-1,0,0)),.1)
        row.append((z,round(hit.x*1000,2) if hit is not None else None))
    print('Positive shell at y',y,row)
