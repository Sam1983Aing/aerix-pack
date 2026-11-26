"""Validate smooth underside rims and preserve the completed V20 exterior."""
import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2]
PANELS={'BELLY_SPINE','BELLY_SERVICE_PANEL','BELLY_SENSOR_BRIDGE','BELLY_PANEL_REVEAL'}
def revised(name):return name in PANELS or name.startswith(('DOWN_SENSOR_HOUSING_','DOWN_SENSOR_EDGE_','DOWN_SENSOR_RETAINING_','DOWN_SENSOR_BAFFLE_','DOWN_SENSOR_INNER_TRACE_'))
def snapshot():
 deps=bpy.context.evaluated_depsgraph_get();result={}
 for o in bpy.context.scene.objects:
  if o.type not in {'MESH','CURVE','FONT'} or o.hide_render or o.name=='STUDIO_GROUND' or revised(o.name):continue
  ev=o.evaluated_get(deps);m=ev.to_mesh();result[o.name]=([tuple(ev.matrix_world@v.co) for v in m.vertices],[i.vertex_index for i in m.loops],[q.name if q else None for q in m.materials]);ev.to_mesh_clear()
 return result
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v20.blend'));before=snapshot();old_shell_normals=[tuple(n.vector) for n in bpy.data.objects['BODY_CRADLE'].data.corner_normals]
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v21.blend'));after=snapshot();unexpected=[n for n in before.keys()|after.keys() if before.get(n)!=after.get(n)];topologies={}
for o in bpy.context.scene.objects:
 if not revised(o.name) or o.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();seen=set();components=0
 for start in bm.verts:
  if start.index in seen:continue
  components+=1;todo=[start]
  while todo:
   v=todo.pop()
   if v.index in seen:continue
   seen.add(v.index);todo.extend(e.other_vert(v) for e in v.link_edges)
 topologies[o.name]={'vertices':len(bm.verts),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'degenerate_faces':sum(f.calc_area()<1e-16 for f in bm.faces),'components':components,'positive_volume':bm.calc_volume(signed=True)>0,'invalid_normals':sum(not all(math.isfinite(x) for x in n.vector) or n.vector.length<.99 for n in o.data.corner_normals)};bm.free()
plate=bpy.data.objects['BELLY_SERVICE_PANEL'];bounds=[[min(v.co[i] for v in plate.data.vertices),max(v.co[i] for v in plate.data.vertices)] for i in range(2)];radial=[]
for sign in [-1,1]:
 m=bpy.data.objects['DOWN_SENSOR_EDGE_'+str(sign)].data;rs=[math.hypot(v.co.x-sign*.025,v.co.y-.0695) for v in m.vertices];radial.append([min(rs),max(rs)])
checks={'other_exterior_geometry_and_materials_preserved':not unexpected,'V20_chassis_normals_preserved':old_shell_normals==[tuple(n.vector) for n in bpy.data.objects['BODY_CRADLE'].data.corner_normals],'closed_connected_rim_and_panel_meshes':all(t['nonmanifold_edges']==0 and t['components']==1 for t in topologies.values()),'positive_mesh_volumes':all(t['positive_volume'] for t in topologies.values()),'no_degenerate_faces':all(t['degenerate_faces']==0 for t in topologies.values()),'valid_surface_normals':all(t['invalid_normals']==0 for t in topologies.values()),'access_panel_footprint_preserved':abs(bounds[0][0]+.0319)<1e-7 and abs(bounds[0][1]-.0319)<1e-7 and abs(bounds[1][0]+.0739)<1e-7 and abs(bounds[1][1]-.0499)<1e-7,'paired_retaining_ring_radii_match':max(abs(a-b) for a,b in zip(radial[0],radial[1]))<1e-7,'sensor_glass_geometry_preserved':all(before['DOWN_SENSOR_COATED_GLASS_'+str(sign)]==after['DOWN_SENSOR_COATED_GLASS_'+str(sign)] for sign in [-1,1]),'intersecting_glass_trace_removed':not any(n.startswith('DOWN_SENSOR_INNER_TRACE_') for n in bpy.data.objects.keys()),'one_rear_port_retained':bpy.data.objects.get('REAR_PORT_MOUNT') is not None and not any(n.startswith('BELLY_PORT_') for n in bpy.data.objects.keys())}
report={'checks':checks,'preserved_objects':len(before),'unexpected_changes':unexpected,'rebuilt_meshes':topologies,'access_panel_xy_bounds':bounds,'retaining_ring_inner_outer_radii_m':radial};(R/'renders/exterior-v21/validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True);assert all(checks.values())
