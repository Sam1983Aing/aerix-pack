import bpy,json
from pathlib import Path
from mathutils import Vector,kdtree
R=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v19.blend'))
for name in ['BODY_CRADLE','BODY_SHELL_TOP','SHELL_SEAM_-1','SHELL_SEAM_1','HINGE_ROTATING_COLLAR_RL','HINGE_ROTATING_COLLAR_RR']:
 o=bpy.data.objects.get(name)
 print('OBJECT',name, 'matrix',str(o.matrix_world),'modifiers',[(m.name,m.type) for m in o.modifiers],flush=True)
o=bpy.data.objects['BODY_CRADLE'];kd=kdtree.KDTree(len(o.data.vertices))
for v in o.data.vertices:kd.insert(v.co,v.index)
kd.balance();diff=[]
for v in o.data.vertices:
 p=v.co
 if p.x<-.025 and .045<p.y<.12 and p.z>.049:
  q=p.copy();q.x*=-1;_,ind,dist=kd.find(q);diff.append((dist,tuple(p)))
print('REAR_MIRROR',len(diff),'max',max(diff),'worst',sorted(diff,reverse=True)[:15],flush=True)
for y in [-.05,0,.045,.060,.073,.082,.094,.106]:
 for z in [.062,.075,.087,.089,.091,.093]:
  hits=[]
  for sign in [-1,1]:
   p=Vector((sign*.15,y,z));hit,loc,n,fi=o.ray_cast(p,Vector((-sign,0,0)))
   hits.append((sign,tuple(loc),tuple(n),fi) if hit else None)
  print('SURFACE',y,z,hits,flush=True)
print('COMPLETE',flush=True)
deps=bpy.context.evaluated_depsgraph_get()
for y,z in [(.060,.075),(.062,.081),(.061,.068),(.02,.091),(-.04,.0911),(0,.0643)]:
 for sign in [-1,1]:
  hits=[]
  for o in bpy.context.scene.objects:
   if o.type not in {'MESH','CURVE','FONT'} or o.hide_render:continue
   e=o.evaluated_get(deps);me=e.to_mesh()
   if not me:continue
   from mathutils.bvhtree import BVHTree
   t=BVHTree.FromPolygons([e.matrix_world@v.co for v in me.vertices],[tuple(p.vertices) for p in me.polygons]);e.to_mesh_clear()
   p,n,i,d=t.ray_cast(Vector((sign*.14,y,z)),Vector((-sign,0,0)),.14)
   if p is not None:hits.append((d,o.name,tuple(p),tuple(n)))
  print('OVERLAY_HITS',sign,y,z,sorted(hits),flush=True)
