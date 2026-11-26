import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v24.blend'))
deps=bpy.context.evaluated_depsgraph_get();out={};trees={}
for name in ['BODY_CRADLE','BODY_SHELL_TOP','REAR_FASCIA','REAR_HOOD_RETURN']:
 o=bpy.data.objects[name];ev=o.evaluated_get(deps);m=ev.to_mesh();vs=[ev.matrix_world@v.co for v in m.vertices]
 trees[name]=BVHTree.FromPolygons(vs,[tuple(p.vertices) for p in m.polygons]);out[name]={'vertices':len(vs),'faces':len(m.polygons),'modifiers':[(q.name,q.type) for q in o.modifiers],'materials':[q.name if q else None for q in m.materials],'bounds':[[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)]}
 if name=='BODY_CRADLE':
  out[name]['rear_faces']=[{'i':p.index,'coords':[list(vs[i]) for i in p.vertices],'normal':list(p.normal),'material':m.materials[p.material_index].name} for p in m.polygons if p.center.y>.120 and p.center.z<.071]
 ev.to_mesh_clear()
probes=[]
for x in [0,.025,.04,.045,.048,.05,.052,.055]:
 for z in [.048,.050,.052,.054,.056,.060,.070,.082,.088]:
  hits={}
  for name,t in trees.items():
   p,n,i,d=t.ray_cast(Vector((x,.180,z)),Vector((0,-1,0)),.075)
   if p is not None:hits[name]={'point':list(p),'normal':list(n),'face':i}
  probes.append({'x':x,'z':z,'hits':hits})
report={'objects':out,'probes':probes};(R/'renders/exterior-v25/native-before.json').write_text(json.dumps(report,indent=2));print({n:{k:v for k,v in q.items() if k!='rear_faces'} for n,q in out.items()},flush=True)
