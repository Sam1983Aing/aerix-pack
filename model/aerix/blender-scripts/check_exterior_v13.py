"""Check continuous rear chassis connections, nesting, symmetry and preserved exterior parts."""
import bpy,bmesh,json,re
from pathlib import Path
from mathutils import Vector,kdtree
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
def revised(name):return name=='BODY_CRADLE' or (name.startswith(('HINGE_','ARM_')) and re.search(r'_R[LR](?:_|$)',name))
def coords(ob,deps):
 ev=ob.evaluated_get(deps);me=ev.to_mesh();vs=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear();return vs
def snapshot():
 deps=bpy.context.evaluated_depsgraph_get();result={}
 for ob in bpy.context.scene.objects:
  if ob.type not in {'MESH','CURVE','FONT'} or ob.hide_render or ob.name=='STUDIO_GROUND' or revised(ob.name):continue
  ev=ob.evaluated_get(deps);me=ev.to_mesh();result[ob.name]=([tuple(ev.matrix_world@v.co) for v in me.vertices],[p.vertex_index for p in me.loops],[m.name if m else None for m in me.materials]);ev.to_mesh_clear()
 return result
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v12.blend'));before=snapshot();deps=bpy.context.evaluated_depsgraph_get();front_before=[p for p in coords(bpy.data.objects['BODY_CRADLE'],deps) if p.y<.038]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v13.blend'));after=snapshot();deps=bpy.context.evaluated_depsgraph_get();s=bpy.context.scene
errors={};unexpected=[]
for name in before.keys()|after.keys():
 if name not in before or name not in after:unexpected.append(name);continue
 a,b=before[name],after[name]
 if len(a[0])!=len(b[0]) or a[1:]!=b[1:]:unexpected.append(name);continue
 errors[name]=max((Vector(x)-Vector(y)).length for x,y in zip(a[0],b[0]))
 if errors[name]>1e-7:unexpected.append(name)
cradle=bpy.data.objects['BODY_CRADLE'];ev=cradle.evaluated_get(deps);me=ev.to_mesh();bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();seen=set();components=[]
for start in bm.verts:
 if start.index in seen:continue
 todo=[start];size=0
 while todo:
  v=todo.pop()
  if v.index in seen:continue
  seen.add(v.index);size+=1;todo.extend(e.other_vert(v) for e in v.link_edges)
 components.append(size)
nonmanifold=sum(not e.is_manifold for e in bm.edges);surface=BVHTree.FromBMesh(bm);bm.free();ev.to_mesh_clear()
all_cradle=coords(cradle,deps);tree=kdtree.KDTree(len(all_cradle))
for i,p in enumerate(all_cradle):tree.insert(p,i)
tree.balance();front_error=max(tree.find(p)[2] for p in front_before)
# Actual lower structural material spans the former gaps on both sides.
bridge_hits=[];bridge_points=[]
for sign in [-1,1]:
 for y in [.077,.086,.095]:
  for x in [.046,.051,.056,.061,.066,.071]:
   hit,p,n,i=ev.ray_cast(Vector((sign*x,y,0)),Vector((0,0,1)));bridge_hits.append(hit);bridge_points.append([sign*x,y,p.z if hit else None])
# Measure bilateral surfaces against the opposite half, allowing Boolean tessellation variation.
mirror_samples=[p for p in all_cradle if p.x>.038 and .043<p.y<.114]
mirror_error=max(tree.find(Vector((-p.x,p.y,p.z)))[2] for p in mirror_samples)
surface_mirror_error=max(surface.find_nearest(Vector((-p.x,p.y,p.z)))[3] for p in mirror_samples)
roots=[bpy.data.objects['ARM_'+tag+'_ROOT'] for tag in ['RL','RR']]
checks={'approved_shell_front_arms_optics_motors_and_blades_preserved':not unexpected,'front_cradle_surface_preserved':front_error<1e-6,'cradle_and_rear_mounts_one_connected_mesh':len(components)==1,'structural_mesh_manifold':nonmanifold==0,'consistent_chassis_material':len(cradle.data.materials)==1 and cradle.data.materials[0].name=='Graphite' and all(p.material_index==0 for p in cradle.data.polygons),'paired_mount_surfaces_match_within_0_05mm':surface_mirror_error<.00005,'solid_lower_bridges_on_both_sides':all(bridge_hits),'rear_pivots_nested_at_70mm':all(abs(abs(o.location.x)-.070)<1e-7 for o in roots),'rear_moving_collars_remain_arm_children':all(bpy.data.objects['HINGE_ROTATING_COLLAR_'+tag].parent==bpy.data.objects['ARM_'+tag+'_ROOT'] for tag in ['RL','RR']),'separate_floating_rear_mount_plates_removed':all(bpy.data.objects.get('HINGE_CHASSIS_MOUNT_'+tag) is None for tag in ['RL','RR'])}
report={'checks':checks,'preserved_objects':len(before),'unexpected_changes':unexpected,'max_preserved_world_error_m':max(errors.values()),'front_cradle_error_m':front_error,'chassis_component_vertex_counts':components,'nonmanifold_edges':nonmanifold,'rear_mirror_nearest_vertex_error_m':mirror_error,'rear_mirror_surface_error_m':surface_mirror_error,'bridge_samples':bridge_points}
(ROOT/'renders/exterior-v13/validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));assert all(checks.values())
