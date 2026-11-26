import bpy,bmesh,math,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def snapshot():
 deps=bpy.context.evaluated_depsgraph_get();out={}
 for o in bpy.context.scene.objects:
  if o.type not in {'MESH','CURVE','FONT'} or o.hide_render or o.name in {'STUDIO_GROUND','BODY_CRADLE','REAR_FASCIA'}:continue
  ev=o.evaluated_get(deps);m=ev.to_mesh();payload=([tuple(ev.matrix_world@v.co) for v in m.vertices],[l.vertex_index for l in m.loops],[tuple(n.vector) for n in m.corner_normals],[q.name if q else None for q in m.materials],o.parent.name if o.parent else None);out[o.name]=hashlib.sha256(repr(payload).encode()).hexdigest();ev.to_mesh_clear()
 return out
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v24.blend'));before=snapshot();old_body={tuple(v.co) for v in bpy.data.objects['BODY_CRADLE'].data.vertices if v.co.y<.126};old_fascia=[tuple(v.co) for v in bpy.data.objects['REAR_FASCIA'].data.vertices]
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v25.blend'));after=snapshot();unexpected=[n for n in before.keys()|after.keys() if before.get(n)!=after.get(n)];topology={}
for name in ['BODY_CRADLE','REAR_FASCIA']:
 m=bpy.data.objects[name].data;bm=bmesh.new();bm.from_mesh(m);bm.verts.ensure_lookup_table();seen=set();components=0
 for start in bm.verts:
  if start.index in seen:continue
  components+=1;todo=[start]
  while todo:
   v=todo.pop()
   if v.index in seen:continue
   seen.add(v.index);todo.extend(e.other_vert(v) for e in v.link_edges)
 topology[name]={'vertices':len(bm.verts),'components':components,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'degenerate_faces':sum(f.calc_area()<1e-16 for f in bm.faces),'positive_volume':bm.calc_volume(signed=True)>0,'invalid_normals':sum(not all(math.isfinite(x) for x in n.vector) or n.vector.length<.99 for n in m.corner_normals)};bm.free()
checks={'other_geometry_material_assignments_normals_and_hierarchy_preserved':not unexpected,'body_coordinates_outside_rear_preserved':old_body=={tuple(v.co) for v in bpy.data.objects['BODY_CRADLE'].data.vertices if v.co.y<.126},'fascia_geometry_and_apertures_preserved':old_fascia==[tuple(v.co) for v in bpy.data.objects['REAR_FASCIA'].data.vertices],'closed_connected_positive_meshes':all(t['components']==1 and t['nonmanifold_edges']==0 and t['positive_volume'] for t in topology.values()),'no_degenerate_faces_or_invalid_normals':all(t['degenerate_faces']==0 and t['invalid_normals']==0 for t in topology.values()),'single_rear_port_preserved':not any(o.name.startswith('BELLY_PORT_') for o in bpy.data.objects)}
report={'checks':checks,'preserved_objects':len(before),'unexpected_changes':unexpected,'topology':topology};(R/'renders/exterior-v25/validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True);assert all(checks.values())
