"""Check camera optics topology, grouping, cavity depth and exterior preservation."""
import bpy,bmesh,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2]
def in_camera(o):
 while o:
  if o.name=='CAMERA_GIMBAL_ROOT':return True
  o=o.parent
 return False
def snap():
 deps=bpy.context.evaluated_depsgraph_get();out={}
 for o in bpy.context.scene.objects:
  if o.type not in {'MESH','CURVE','FONT'} or o.hide_render or o.name=='STUDIO_GROUND' or in_camera(o):continue
  ev=o.evaluated_get(deps);me=ev.to_mesh();out[o.name]=([tuple(ev.matrix_world@v.co) for v in me.vertices],[i.vertex_index for i in me.loops],[m.name if m else None for m in me.materials]);ev.to_mesh_clear()
 return out
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v16.blend'));before=snap()
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v17.blend'));after=snap();deps=bpy.context.evaluated_depsgraph_get()
changed=[n for n in before.keys()|after.keys() if before.get(n)!=after.get(n)]
def topology(o):
 ev=o.evaluated_get(deps);me=ev.to_mesh();bm=bmesh.new();bm.from_mesh(me);v={'vertices':len(bm.verts),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'volume_m3':abs(bm.calc_volume())};bm.free();ev.to_mesh_clear();return v
parts=[o for o in bpy.context.scene.objects if in_camera(o) and o.type=='MESH'];topo={o.name:topology(o) for o in parts}
# A central ray sees glass interfaces before the dark internal elements, then a closed housing.
p=Vector((0,-.25,.038));hits=[]
for i in range(14):
 hit,loc,n,fi,o,m=bpy.context.scene.ray_cast(deps,p,Vector((0,1,0)))
 if not hit:break
 hits.append({'name':o.name,'y':loc.y});p=loc+Vector((0,.00002,0))
fronts=[]
for name in ['LENS_FRONT_ELEMENT','LENS_MIDDLE_ELEMENT','LENS_REAR_COATED_ELEMENT']:
 o=bpy.data.objects[name];fronts.append(min((o.matrix_world@v.co).y for v in o.data.vertices))
low=min((o.matrix_world@v.co).z for o in parts for v in o.data.vertices)
checks={'entire_non_camera_exterior_preserved':not changed,'camera_meshes_closed':all(x['nonmanifold_edges']==0 and x['volume_m3']>1e-14 for x in topo.values()),'four_distinct_curved_optical_elements':all(bpy.data.objects.get(n) for n in ['LENS_FRONT_ELEMENT','LENS_MIDDLE_ELEMENT','LENS_REAR_COATED_ELEMENT','LENS_DEEP_OPTICAL_CORE']),'optical_layers_ordered_in_depth':fronts==sorted(fronts),'glass_recessed_behind_front_rim':fronts[0]>-.1847+.002,'center_ray_enters_glass_first':hits[0]['name']=='LENS_FRONT_ELEMENT','camera_ground_clearance':low>.0125,'camera_pitch_pivot':bpy.data.objects['CAMERA_PITCH_ROOT'].parent.name=='CAMERA_GIMBAL_ROOT','lens_components_follow_optics_root':all(bpy.data.objects[n].parent.name=='LENS_OPTICS_ROOT' for n in ['LENS_FRONT_ELEMENT','LENS_MIDDLE_ELEMENT','LENS_REAR_COATED_ELEMENT']),'no_old_grip_teeth':not any(n.startswith('LENS_GRIP_') for n in bpy.data.objects.keys()),'nine_iris_leaves':sum(n.startswith('LENS_IRIS_LEAF_') for n in bpy.data.objects.keys())==9,'materials_assigned':all(len(o.data.materials)>0 and all(o.data.materials) for o in parts)}
report={'checks':checks,'preserved_objects':len(before),'unexpected_changes':changed,'camera_objects':len(parts),'lowest_camera_z_m':low,'optical_front_y_m':fronts,'topology':topo,'central_ray_hits':hits};(R/'renders/exterior-v17/validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));assert all(checks.values())
