"""Validate front-lip separation and preserve approved exterior assemblies."""
import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2]
def snapshot():
 deps=bpy.context.evaluated_depsgraph_get();result={}
 for o in bpy.context.scene.objects:
  if o.type not in {'MESH','CURVE','FONT'} or o.hide_render or o.name in {'STUDIO_GROUND','BODY_CRADLE','BODY_SHELL_TOP'}:continue
  ev=o.evaluated_get(deps);m=ev.to_mesh();result[o.name]=([tuple(ev.matrix_world@v.co) for v in m.vertices],[i.vertex_index for i in m.loops],[q.name if q else None for q in m.materials]);ev.to_mesh_clear()
 return result
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v21.blend'));before=snapshot();oldroof=[tuple(v.co) for v in bpy.data.objects['BODY_SHELL_TOP'].data.vertices];oldcradle=[tuple(v.co) for v in bpy.data.objects['BODY_CRADLE'].data.vertices];oldnormals=[tuple(n.vector) for n in bpy.data.objects['BODY_CRADLE'].data.corner_normals]
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v22.blend'));after=snapshot();unexpected=[n for n in before.keys()|after.keys() if before.get(n)!=after.get(n)];topology={}
for name in ['BODY_CRADLE','BODY_SHELL_TOP']:
 o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();seen=set();components=0
 for start in bm.verts:
  if start.index in seen:continue
  components+=1;todo=[start]
  while todo:
   v=todo.pop()
   if v.index in seen:continue
   seen.add(v.index);todo.extend(e.other_vert(v) for e in v.link_edges)
 topology[name]={'vertices':len(bm.verts),'components':components,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'degenerate_faces':sum(f.calc_area()<1e-16 for f in bm.faces),'positive_volume':bm.calc_volume(signed=True)>0,'invalid_normals':sum(not all(math.isfinite(x) for x in n.vector) or n.vector.length<.99 for n in o.data.corner_normals)};bm.free()
roof=bpy.data.objects['BODY_SHELL_TOP'];cradle=bpy.data.objects['BODY_CRADLE'];me=cradle.data
outside_changes=[v.index for v in me.vertices if (oldcradle[v.index][1]>=-.124 or oldcradle[v.index][2]<=.088) and tuple(v.co)!=oldcradle[v.index]]
def angle_degrees(a,b):
 dot=sum(x*y for x,y in zip(a,b));denom=math.sqrt(sum(x*x for x in a)*sum(y*y for y in b));return math.degrees(math.acos(max(-1,min(1,dot/denom))))
normal_error=max(angle_degrees(oldnormals[i],n.vector) for i,n in enumerate(me.corner_normals) if me.vertices[me.loops[i].vertex_index].co.y>=-.120 or me.vertices[me.loops[i].vertex_index].co.z<=.0875)
surfaces={}
for o in [roof,cradle]:surfaces[o.name]=BVHTree.FromPolygons([v.co for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons])
boundary=list(roof['top_boundary_edges']);probes=[]
for ia,ib in zip(boundary[::2],boundary[1::2]):
 a=roof.data.vertices[ia].co;b=roof.data.vertices[ib].co
 if max(a.y,b.y)>-.136 or ia%5:continue
 q=(a+b)*.5;d=b-a;n=Vector((d.y,-d.x,0)).normalized()
 if n.dot(Vector((q.x,q.y,0)))<0:n.negate()
 q.z-=.0010;hits={}
 for name,t in surfaces.items():
  p,no,index,dist=t.ray_cast(q+n*.003,-n,.012)
  if p is not None:hits[name]=dist
 if len(hits)==2:probes.append({'x':q.x,'clearance_mm':1000*(hits['BODY_CRADLE']-hits['BODY_SHELL_TOP'])})
checks={'other_exterior_geometry_materials_preserved':not unexpected,'roof_silhouette_exactly_preserved':oldroof==[tuple(v.co) for v in roof.data.vertices],'chassis_changes_only_at_front_lip':not outside_changes,'previous_chassis_normals_preserved_within_0_05_degrees':normal_error<.05,'closed_connected_positive_meshes':all(t['components']==1 and t['nonmanifold_edges']==0 and t['positive_volume'] for t in topology.values()),'no_degenerate_faces_or_invalid_normals':all(t['degenerate_faces']==0 and t['invalid_normals']==0 for t in topology.values()),'front_clearance_above_0_30_mm':len(probes)>20 and min(p['clearance_mm'] for p in probes)>.30,'stereo_optics_and_visor_preserved':all(before[n]==after[n] for n in before if n.startswith(('STEREO_','FRONT_VISOR','STATUS_LED'))),'one_rear_port_retained':bpy.data.objects.get('REAR_PORT_MOUNT') is not None and not any(n.startswith('BELLY_PORT_') for n in bpy.data.objects.keys())}
report={'checks':checks,'preserved_objects':len(before),'unexpected_changes':unexpected,'topology':topology,'maximum_other_chassis_normal_error_degrees':normal_error,'front_clearance_probes':probes};(R/'renders/exterior-v22/validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True);assert all(checks.values())
