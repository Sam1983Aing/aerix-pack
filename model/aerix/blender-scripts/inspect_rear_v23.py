import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v22.blend'))
deps=bpy.context.evaluated_depsgraph_get();surfaces={};objects=[]
for o in bpy.context.scene.objects:
 if o.name not in ['BODY_SHELL_TOP','BODY_CRADLE'] and not (o.name.startswith('REAR_') and not o.name.startswith('REAR_LEG_')):continue
 if o.type not in {'MESH','CURVE'}:continue
 e=o.evaluated_get(deps);me=e.to_mesh();vs=[e.matrix_world@v.co for v in me.vertices];surfaces[o.name]=BVHTree.FromPolygons(vs,[tuple(p.vertices) for p in me.polygons]);objects.append({'name':o.name,'vertices':len(me.vertices),'modifiers':[(m.name,m.type) for m in o.modifiers],'bounds':[[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)],'materials':[m.name for m in me.materials]});e.to_mesh_clear()
results=[]
for x in [0,.018,.028,.041,.046]:
 for z in [.049,.052,.0595,.0665,.0692,.072,.079,.086,.089,.090,.0925,.094]:
  hits=[]
  for name,t in surfaces.items():
   p,n,i,d=t.ray_cast(Vector((x,.20,z)),Vector((0,-1,0)),.08)
   if p is not None:hits.append({'object':name,'distance_m':d,'point':list(p),'normal':list(n)})
  results.append({'x':x,'z':z,'hits':sorted(hits,key=lambda a:a['distance_m'])})
(R/'renders/exterior-v23/rear-before-probes.json').write_text(json.dumps({'objects':objects,'probes':results},indent=2));print(json.dumps(objects),flush=True)
