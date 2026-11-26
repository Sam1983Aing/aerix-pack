"""Diagnose the clearance between the deep nose pocket and the optical barrel."""
import bpy
import sys
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from check_v04_assembly import local_meshes,world_solids
def inspect(group,label):
    s=world_solids(local_meshes(group),{})
    a=s['Camera.lens_barrel']; b=s['Shell.moulded_fuselage']
    hits=a.tree.overlap(b.tree)
    print(label,'overlap',len(hits), 'bounds',a.lo,a.hi,flush=True)
    print('first',a.vertices[0],b.tree.find_nearest(a.vertices[0]),flush=True)
    nearest=min((b.tree.find_nearest(p)[3],i) for i,p in enumerate(a.vertices))
    print('min barrel vertex to shell',nearest[0]*1000,a.vertices[nearest[1]],flush=True)
    inside=0
    for direction in ((1,.123,.245),(-.2,.1,-1),(-1,-.42,.3)):
        d=Vector(direction).normalized()
        q=a.vertices[0]+0*d
        count=0
        for it in range(100):
            h=b.tree.ray_cast(q,d)[0]
            if h is None: break
            count+=1;q=h+.0000001*d
        inside+=count%2
        print('ray intersections',count,flush=True)
    print('inside votes',inside,flush=True)
for v in ('v14','v14a'):
    bpy.ops.wm.open_mainfile(filepath=str(root/f'blender/drone-{v}.blend'))
    inspect(bpy.context.scene,v+' native')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps=30
    bpy.ops.import_scene.gltf(filepath=str(root/f'exports/drone-{v}.glb'))
    inspect(bpy.context.scene,v+' glb')
