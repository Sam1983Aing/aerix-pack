"""Verify arm-only scope, real hinge recesses, mirrored hardware and preserved rotors."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,kdtree
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[2]
def revised(name):return name.startswith(('HINGE_','ARM_'))
def snapshot():
 deps=bpy.context.evaluated_depsgraph_get();result={}
 for ob in bpy.context.scene.objects:
  if ob.type not in {'MESH','CURVE','FONT'} or ob.hide_render or ob.name=='STUDIO_GROUND' or revised(ob.name):continue
  ev=ob.evaluated_get(deps);me=ev.to_mesh();result[ob.name]=([tuple(ev.matrix_world@v.co) for v in me.vertices],[p.vertex_index for p in me.loops],[m.name if m else None for m in me.materials]);ev.to_mesh_clear()
 return result
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v11.blend'));before=snapshot()
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v12.blend'));after=snapshot();s=bpy.context.scene;deps=bpy.context.evaluated_depsgraph_get()
errors={};unexpected=[]
for name in before.keys()|after.keys():
 if name not in before or name not in after:unexpected.append(name);continue
 a,b=before[name],after[name]
 if len(a[0])!=len(b[0]) or a[1:]!=b[1:]:unexpected.append(name);continue
 errors[name]=max((Vector(x)-Vector(y)).length for x,y in zip(a[0],b[0]))
 if errors[name]>1e-7:unexpected.append(name)
def coords(ob):
 ev=ob.evaluated_get(deps);me=ev.to_mesh();vs=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear();return vs
mirrors={}
for pair in [('FL','FR'),('RL','RR')]:
 for part in ['ARM_','ARM_INLAY_','HINGE_CAP_','HINGE_ROTATING_COLLAR_','HINGE_CHASSIS_MOUNT_']:
  a=coords(bpy.data.objects[part+pair[0]]);b=coords(bpy.data.objects[part+pair[1]]);tree=kdtree.KDTree(len(a))
  for i,p in enumerate(a):tree.insert(p,i)
  tree.balance();mirrors[part+pair[0]]=max(tree.find(Vector((-p.x,p.y,p.z)))[2] for p in b)
parenting=[];recess=[];gaps=[]
for tag in ['FL','FR','RL','RR']:
 arm=bpy.data.objects['ARM_'+tag+'_ROOT'];pivot=arm.location
 parenting.append(bpy.data.objects['HINGE_CHASSIS_MOUNT_'+tag].parent.name=='DRONE_ROOT' and bpy.data.objects['HINGE_FIXED_AXLE_'+tag].parent.name=='DRONE_ROOT' and bpy.data.objects['HINGE_ROTATING_COLLAR_'+tag].parent==arm and bpy.data.objects['ARM_'+tag].parent==arm)
 cap=bpy.data.objects['HINGE_CAP_'+tag].evaluated_get(deps);inv=cap.matrix_world.inverted();origin=inv@Vector((pivot.x,pivot.y,.12));direction=inv.to_3x3()@Vector((0,0,-1));recess.append(not cap.ray_cast(origin,direction)[0])
 a=max(p.z for p in coords(bpy.data.objects['HINGE_CHASSIS_MOUNT_'+tag]));b=min(p.z for p in coords(bpy.data.objects['HINGE_ROTATING_COLLAR_'+tag]));gaps.append(b-a)
points=[]
for ob in s.objects:
 if ob.type in {'MESH','CURVE','FONT'} and not ob.hide_render and ob.name!='STUDIO_GROUND':points.extend(world_to_camera_view(s,bpy.data.objects['CAM_hero'],p) for p in coords(ob))
checks={'body_optics_motors_blades_and_rear_preserved':not unexpected,'bilateral_matching_beams_and_hinges':max(mirrors.values())<1e-5,'four_fixed_mounts_and_separate_rotating_collars':all(parenting),'four_true_cap_counterbores':all(recess),'positive_mount_to_rotor_clearance':min(gaps)>.0007,'eight_blades':sum(o.name.startswith('BLADE_') for o in s.objects)==8,'four_independent_rotors':sum(o.name.startswith('PROPELLER_') for o in s.objects)==4,'hero_not_cropped':all(0<p.x<1 and 0<p.y<1 and p.z>0 for p in points)}
report={'checks':checks,'preserved_objects':len(before),'maximum_preserved_world_error_m':max(errors.values()),'unexpected_changes':unexpected,'mirror_errors_m':mirrors,'mount_rotor_gaps_m':gaps}
(ROOT/'renders/exterior-v12/validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));assert all(checks.values())
