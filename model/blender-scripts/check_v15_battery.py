"""Measure seated battery clearance, the rear withdrawal sweep and source envelopes."""
from pathlib import Path
import json,sys
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
revision=Path(bpy.data.filepath).stem.removeprefix('drone-')
assert revision in ('v15','v16','v17','v18')
interior_collection='V15 | Interior blockout' if revision=='v15' else revision.upper()+' | Interior'
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'scripts'))
from check_v04_assembly import Solid
def solid(o):
    m=o.data;m.calc_loop_triangles()
    return Solid([o.matrix_world@v.co for v in m.vertices],[t.vertices[:] for t in m.loop_triangles])
def mesh_distance(a,b):
    """Near triangle pairs, vertex/face and edge/edge minima, world metres."""
    bounds=np.array([b.lo,b.hi])
    ap=[p for p in a.vertices if all(bounds[0,i]-.004<p[i]<bounds[1,i]+.004 for i in range(3))]
    bp=[p for p in b.vertices if all(a.lo[i]-.004<p[i]<a.hi[i]+.004 for i in range(3))]
    distances=[(b.tree.find_nearest(p)[3],tuple(p)) for p in ap]+[(a.tree.find_nearest(p)[3],tuple(p)) for p in bp]
    if not distances:return None
    best,where=min(distances)
    near=BVHTree.FromPolygons(a.vertices,a.faces,all_triangles=True,epsilon=best+.000001).overlap(b.tree)
    if not near:return best,where
    ia,ib=np.array(near).T
    av=np.array(a.vertices)[np.array(a.faces)[ia]];bv=np.array(b.vertices)[np.array(b.faces)[ib]]
    def dot(a,b):return np.einsum('ij,ij->i',a,b)
    for i in range(3):
        for j in range(3):
            p=av[:,i];q=bv[:,j];u=av[:,(i+1)%3]-p;v=bv[:,(j+1)%3]-q;r=p-q
            aa=dot(u,u);bb=dot(u,v);cc=dot(v,v);dd=dot(u,r);ee=dot(v,r);det=aa*cc-bb*bb
            safe=det>1e-26
            s=np.where(safe,(bb*ee-cc*dd)/np.where(safe,det,1),0)
            t=np.where(safe,(aa*ee-bb*dd)/np.where(safe,det,1),0)
            good=safe&(s>=0)&(s<=1)&(t>=0)&(t<=1)
            if not good.any():continue
            vec=r+s[:,None]*u-t[:,None]*v
            ds=np.where(good,dot(vec,vec),np.inf);k=ds.argmin()
            if ds[k]<best*best:best=float(np.sqrt(ds[k]));where=tuple(p[k]+s[k]*u[k])
    return best,where
g=bpy.data.collections[revision.upper()+' | Aircraft'];inside=bpy.data.collections[interior_collection]
bpy.context.scene.frame_set(1)
packs={o.name:solid(o) for o in inside.objects if o.name.startswith('Battery.')}
other={o.name:solid(o) for o in list(g.objects)+list(inside.objects) if o.type=='MESH' and o.name not in packs}
walls=['Shell.roof_cover','Shell.belly_cover','Shell.middle_frame','Shell.battery_door']
gaps=[]
for n,a in packs.items():
    for w in walls:
        result=mesh_distance(a,other[w])
        if result:
            val,pt=result;gaps.append((round(val*1000,5),n,w,[round(x*1000,3) for x in pt]))
print('WALL GAPS',sorted(gaps),flush=True)
hits={}
for j in range(0,169):
    offset=-j*.0005
    for n,s in packs.items():
        a=Solid([v+Vector((0,offset,0)) for v in s.vertices],s.faces)
        for k,b in other.items():
            if k=='Shell.battery_door' or a.gap_box(b)>1e-8:continue
            if a.contacts(b):hits.setdefault(k,[]).append(-offset*1000)
size=[round((max(v.hi[i] for v in packs.values())-min(v.lo[i] for v in packs.values()))*1000,3) for i in (1,0,2)]
report={'battery_assembly_LWH_mm':size,'minimum_pack_to_casting_mm':min(gaps),'all_casting_gaps_mm':sorted(gaps),
        'withdrawal_step_mm':.5,'travel_mm':84,'positions':169,'obstructions_with_door_removed':{k:[round(min(v),2),round(max(v),2)] for k,v in hits.items()}}
(root/f'measurements/{revision}-battery.json').write_text(json.dumps(report,indent=2)+'\n')
print('BATTERY',size,report['obstructions_with_door_removed'],flush=True)
assert size==[75.,38.7,19.6] and not hits and min(gaps)[0]>0,report

