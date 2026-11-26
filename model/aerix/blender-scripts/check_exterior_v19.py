"""Verify the removed connector, welded shell and retained exterior details."""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2]
def snapshot():
 deps=bpy.context.evaluated_depsgraph_get();out={}
 for o in bpy.context.scene.objects:
  if o.type not in {'MESH','CURVE','FONT'} or o.hide_render or o.name in {'STUDIO_GROUND','BODY_CRADLE'} or o.name.startswith('BELLY_PORT_'):continue
  ev=o.evaluated_get(deps);me=ev.to_mesh();out[o.name]=([tuple(ev.matrix_world@v.co) for v in me.vertices],[i.vertex_index for i in me.loops],[m.name if m else None for m in me.materials]);ev.to_mesh_clear()
 return out
def untouched_chassis():
 me=bpy.data.objects['BODY_CRADLE'].data;result={}
 for p in me.polygons:
  if any(abs(me.vertices[i].co.x)<.0084 and abs(me.vertices[i].co.y-.1215)<.0039 and me.vertices[i].co.z<.055 for i in p.vertices):continue
  result[tuple(sorted(tuple(me.vertices[i].co) for i in p.vertices))]={tuple(me.vertices[me.loops[li].vertex_index].co):tuple(me.corner_normals[li].vector) for li in p.loop_indices}
 return result
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v13.blend'));source=BVHTree.FromObject(bpy.data.objects['BODY_CRADLE'],bpy.context.evaluated_depsgraph_get())
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v18.blend'));before=snapshot();oldskin=untouched_chassis()
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v19.blend'));after=snapshot();newskin=untouched_chassis();deps=bpy.context.evaluated_depsgraph_get();o=bpy.data.objects['BODY_CRADLE'];ev=o.evaluated_get(deps);me=ev.to_mesh();bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();seen=set();components=[]
for start in bm.verts:
 if start.index in seen:continue
 todo=[start];size=0
 while todo:
  v=todo.pop()
  if v.index in seen:continue
  seen.add(v.index);size+=1;todo.extend(e.other_vert(v) for e in v.link_edges)
 components.append(size)
topo={'vertices':len(bm.verts),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'degenerate_faces':sum(p.calc_area()<1e-16 for p in bm.faces),'components':components,'invalid_normals':sum(not all(math.isfinite(v) for v in n.vector) or n.vector.length<.99 for n in me.corner_normals)};bm.free();ev.to_mesh_clear()
errors=[];thickness=[]
for i in range(17):
 for j in range(9):
  x=(i-8)*.0008;y=.1215+(j-4)*.0007;hits=[]
  for inner in [False,True]:
   p=Vector((x,y,.059 if inner else -.1));d=Vector((0,0,-1 if inner else 1));expected=source.ray_cast(p,d,1)[0];hit,loc,n,fi=ev.ray_cast(p,d);assert hit and expected is not None;errors.append(abs(loc.z-expected.z));hits.append(loc.z)
  thickness.append(hits[1]-hits[0])
vents=[]
for x in [-.0328,.0328]:
 hit,p,n,i=ev.ray_cast(Vector((x,.1215,-.1)),Vector((0,0,1)));vents.append(not hit or p.z>=.074-1e-6)
unexpected=[n for n in before.keys()|after.keys() if before.get(n)!=after.get(n)]
# Packed 16-bit custom normals incur small rounding when topology changes.
# Require identical surviving faces and less than 0.05 degrees of shading change.
skin_geometry_unchanged=oldskin.keys()==newskin.keys()
skin_normal_error=max((Vector(n)-Vector(newskin[f][v])).length for f,cs in oldskin.items() if f in newskin for v,n in cs.items())
checks={'underside_connector_and_surround_removed':not any(n.startswith('BELLY_PORT_') for n in bpy.data.objects.keys()),'rear_connector_retained':all(bpy.data.objects.get(n) for n in ['REAR_PORT_MOUNT','REAR_PORT_METAL_SHELL','REAR_PORT_TONGUE']),'24_rear_contacts_retained':sum(n.startswith('REAR_PORT_CONTACT_') for n in bpy.data.objects.keys())==24,'other_exterior_objects_preserved':not unexpected,'chassis_outside_repair_preserved':skin_geometry_unchanged and math.degrees(2*math.asin(min(1,skin_normal_error/2)))<.05,'one_closed_chassis_mesh':topo['nonmanifold_edges']==0 and len(components)==1,'valid_surface_normals':topo['invalid_normals']==0,'no_degenerate_faces':topo['degenerate_faces']==0,'repaired_skin_matches_original_curvature':max(errors)<.000005,'positive_shell_thickness':min(thickness)>.0015,'both_underside_vents_open':all(vents)}
report={'checks':checks,'preserved_objects':len(before),'unexpected_changes':unexpected,'untouched_chassis_geometry_equal':skin_geometry_unchanged,'untouched_chassis_max_normal_difference':skin_normal_error,'untouched_chassis_max_normal_angle_degrees':math.degrees(2*math.asin(min(1,skin_normal_error/2))),'topology':topo,'max_surface_error_m':max(errors),'minimum_repaired_thickness_m':min(thickness),'sampled_repair_rays':len(errors)};(R/'renders/exterior-v19/validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True);assert all(checks.values())
