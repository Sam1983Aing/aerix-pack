import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v21.blend'))
deps=bpy.context.evaluated_depsgraph_get();surfaces={}
for name in ['BODY_SHELL_TOP','BODY_CRADLE','FRONT_VISOR_FRAME','FRONT_VISOR','VISOR_LOWER_LIP']:
 o=bpy.data.objects[name];e=o.evaluated_get(deps);me=e.to_mesh();surfaces[name]=BVHTree.FromPolygons([e.matrix_world@v.co for v in me.vertices],[tuple(p.vertices) for p in me.polygons]);e.to_mesh_clear()
 print('OBJECT',name,dict(o.items()),'modifiers',[(m.name,m.type) for m in o.modifiers],flush=True)
results=[]
for x in [0,.02,.045,.058,.064,.067]:
 for z in [.0918,.0925,.093,.0935,.094,.0945,.095,.0955]:
  hits=[]
  for name,t in surfaces.items():
   p,n,i,d=t.ray_cast(Vector((x,-.2,z)),Vector((0,1,0)),.12)
   if p is not None:hits.append({'object':name,'distance_m':d,'point':list(p),'normal':list(n)})
  results.append({'x':x,'z':z,'hits':sorted(hits,key=lambda a:a['distance_m'])})
(R/'renders/exterior-v22/front-before-probes.json').write_text(json.dumps(results,indent=2))
print('FRONT_PROBES',json.dumps([r for r in results if sum(h['object'] in {'BODY_CRADLE','BODY_SHELL_TOP'} for h in r['hits'])==2]),flush=True)
