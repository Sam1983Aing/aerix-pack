"""Validate the four shoulders and preservation of all previously approved geometry."""
import bpy,bmesh,math,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2]
NAMES={'MOTOR_BASE_'+tag for tag in ['FL','FR','RL','RR']}
def snapshot():
 deps=bpy.context.evaluated_depsgraph_get();out={};bases={}
 for o in bpy.context.scene.objects:
  if o.type not in {'MESH','CURVE','FONT'} or o.hide_render or o.name=='STUDIO_GROUND':continue
  ev=o.evaluated_get(deps);me=ev.to_mesh()
  if o.name in NAMES:
   bases[o.name]={'vertices':[tuple(v.co) for v in me.vertices if v.co.z<.08130],'parent':o.parent.name,'normals':[tuple(me.corner_normals[j].vector) for f in me.polygons if all(me.vertices[i].co.z<.08130 for i in f.vertices) for j in f.loop_indices]}
  else:
   payload=([tuple(ev.matrix_world@v.co) for v in me.vertices],[i.vertex_index for i in me.loops],[tuple(n.vector) for n in me.corner_normals],[m.name if m else None for m in me.materials],o.parent.name if o.parent else None)
   out[o.name]=hashlib.sha256(repr(payload).encode()).hexdigest()
  ev.to_mesh_clear()
 return out,bases
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v23.blend'));before,bases_before=snapshot()
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v24.blend'));after,bases_after=snapshot()
unexpected=[n for n in before.keys()|after.keys() if before.get(n)!=after.get(n)]
topology={};max_angle=0
def angle(a,b):return math.degrees(math.acos(max(-1,min(1,sum(x*y for x,y in zip(a,b))/math.sqrt(sum(x*x for x in a)*sum(y*y for y in b))))))
for name in sorted(NAMES):
 me=bpy.data.objects[name].data;bm=bmesh.new();bm.from_mesh(me)
 topology[name]={'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'degenerate_faces':sum(f.calc_area()<1e-16 for f in bm.faces),'positive_volume':bm.calc_volume(signed=True)>0,'invalid_normals':sum(not all(math.isfinite(x) for x in n.vector) or n.vector.length<.99 for n in me.corner_normals)};bm.free()
 for a,b in zip(bases_before[name]['normals'],bases_after[name]['normals']):max_angle=max(max_angle,angle(a,b))
checks={'all_other_geometry_materials_normals_and_parents_preserved':not unexpected,'all_four_lower_legs_preserved_exactly':all(bases_before[n]['vertices']==bases_after[n]['vertices'] for n in NAMES),'lower_leg_normals_within_0_05_degrees':max_angle<.05,'all_four_follow_original_arm_pivots':all(bases_before[n]['parent']==bases_after[n]['parent'] for n in NAMES),'closed_positive_meshes':all(t['nonmanifold_edges']==0 and t['positive_volume'] for t in topology.values()),'no_degenerates_or_invalid_normals':all(t['degenerate_faces']==0 and t['invalid_normals']==0 for t in topology.values()),'shared_clean_motor_support_finish':all([m.name for m in bpy.data.objects[n].data.materials]==['V24 smooth satin motor support'] for n in NAMES)}
report={'checks':checks,'preserved_other_objects':len(before),'unexpected_changes':unexpected,'maximum_preserved_normal_error_degrees':max_angle,'topology':topology};(R/'renders/exterior-v24/validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True);assert all(checks.values())
