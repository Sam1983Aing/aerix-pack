"""Report world locations of actual contacting edges for the V08 fit review."""
from pathlib import Path
import bpy,sys
from mathutils import geometry
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from check_v04_assembly import world_solids,local_meshes
group=bpy.data.collections['V08 | Aircraft']
meshes=local_meshes(group)
cache={}
for f in (1,42,84,120,121):
    bpy.context.scene.frame_set(f)
    solids=world_solids(meshes,cache)
    if f in (1,121):
        for idx in (0,1,2):
            print('Max',f,idx,sorted([(round(a.hi[idx]*1000,3),n) for n,a in solids.items()],reverse=True)[:4])
    hull=solids['Shell.moulded_fuselage']
    for name in ('Leg.front.R','Propeller.blade.RR.2','Arm.RR','Motor.FR'):
        obj=solids[name]
        hits=[]
        for i,j in obj.tree.overlap(hull.tree):
            vs=[obj.vertices[k] for k in obj.faces[i]]
            ws=[hull.vertices[k] for k in hull.faces[j]]
            for tri,target in ((vs,ws),(ws,vs)):
                for a,b in zip(tri,tri[1:]+tri[:1]):
                    d=b-a
                    if d.length<1e-9:continue
                    hit=geometry.intersect_ray_tri(*target,d.normalized(),a)
                    if hit is not None and (hit-a).length<=d.length+1e-9: hits.append(hit)
        if hits:
            print(f,name,[(round(min(p[i] for p in hits)*1000,2),round(max(p[i] for p in hits)*1000,2)) for i in (0,1,2)])
