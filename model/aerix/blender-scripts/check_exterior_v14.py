"""Verify underside apertures, fitted surfaces, hardware, and preserved approved exterior."""
import bpy,bmesh,json
from pathlib import Path
from mathutils import Vector,kdtree
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
def revised(name):return name=='BODY_CRADLE' or name in ['HINGE_CHASSIS_MOUNT_FL','HINGE_CHASSIS_MOUNT_FR'] or name.startswith(('BELLY_','DOWN_SENSOR_','HINGE_UNDER_','ARM_UNDER_'))
def points(ob,deps):
 ev=ob.evaluated_get(deps);me=ev.to_mesh();vs=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear();return vs
def snapshot():
 deps=bpy.context.evaluated_depsgraph_get();out={}
 for ob in bpy.context.scene.objects:
  if ob.type not in {'MESH','CURVE','FONT'} or ob.hide_render or ob.name=='STUDIO_GROUND' or revised(ob.name):continue
  ev=ob.evaluated_get(deps);me=ev.to_mesh();out[ob.name]=([tuple(ev.matrix_world@v.co) for v in me.vertices],[p.vertex_index for p in me.loops],[m.name if m else None for m in me.materials]);ev.to_mesh_clear()
 return out
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v13.blend'));before=snapshot();deps=bpy.context.evaluated_depsgraph_get();old=bpy.data.objects['BODY_CRADLE'];original_floor=BVHTree.FromObject(old,deps);upper_before=[p for p in points(old,deps) if p.z>.078]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v14.blend'));after=snapshot();deps=bpy.context.evaluated_depsgraph_get();s=bpy.context.scene;unexpected=[];max_error=0
for name in before.keys()|after.keys():
 if name not in before or name not in after:unexpected.append(name);continue
 a,b=before[name],after[name]
 if len(a[0])!=len(b[0]) or a[1:]!=b[1:]:unexpected.append(name);continue
 error=max((Vector(x)-Vector(y)).length for x,y in zip(a[0],b[0]));max_error=max(max_error,error)
 if error>1e-7:unexpected.append(name)
def topology(ob):
 ev=ob.evaluated_get(deps);me=ev.to_mesh();bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();seen=set();components=[]
 for start in bm.verts:
  if start.index in seen:continue
  todo=[start];size=0
  while todo:
   v=todo.pop()
   if v.index in seen:continue
   seen.add(v.index);size+=1;todo.extend(e.other_vert(v) for e in v.link_edges)
  components.append(size)
 result={'components':len(components),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'vertices':len(bm.verts)};bm.free();ev.to_mesh_clear();return result
primary=['BODY_CRADLE','BELLY_SPINE','BELLY_SERVICE_PANEL','BELLY_SENSOR_BRIDGE','BELLY_PORT_PAD','HINGE_CHASSIS_MOUNT_FL','HINGE_CHASSIS_MOUNT_FR'];topologies={name:topology(bpy.data.objects[name]) for name in primary}
cradle=bpy.data.objects['BODY_CRADLE'];ev=cradle.evaluated_get(deps);coords=points(cradle,deps);tree=kdtree.KDTree(len(coords))
for i,p in enumerate(coords):tree.insert(p,i)
tree.balance();upper_error=max(tree.find(p)[2] for p in upper_before)
apertures=[(0,-.012),(-.025,.0695),(.025,.0695),(0,.1215),(-.0328,.1215),(.0328,.1215)]
rays=[ev.ray_cast(Vector((x,y,-.03)),Vector((0,0,1))) for x,y in apertures]
# Sensor cavities terminate at z=.062; the other apertures pass fully through the lower cradle.
openings=[not hit or point.z>=limit-1e-6 for (hit,point,normal,idx),limit in zip(rays,[.063,.062,.062,.075,.074,.074])]
fit={}
for name in ['BELLY_SPINE','BELLY_SERVICE_PANEL','BELLY_SENSOR_BRIDGE']:
 ob=bpy.data.objects[name].evaluated_get(deps);me=ob.to_mesh();clearances=[]
 for face in me.polygons:
  if face.normal.z>-.60:continue
  p=face.center;hit,n,i,d=original_floor.ray_cast(Vector((p.x,p.y,-.1)),Vector((0,0,1)),1)
  if hit is not None:clearances.append(hit.z-p.z)
 fit[name]={'minimum_m':min(clearances),'maximum_m':max(clearances)};ob.to_mesh_clear()
checks={'approved_upper_shell_arms_motors_optics_and_rear_details_preserved':not unexpected,'upper_cradle_surface_preserved':upper_error<1e-6,'primary_parts_closed_manifold':all(v['nonmanifold_edges']==0 for v in topologies.values()),'chassis_remains_one_connected_mesh':topologies['BODY_CRADLE']['components']==1,'six_real_underside_apertures_and_recesses':all(openings),'fitted_front_surfaces_clear_the_body':all(v['minimum_m']>-.00002 for v in fit.values()),'two_downward_lens_modules':sum(o.name.startswith('DOWN_SENSOR_COATED_GLASS_') for o in s.objects)==2,'four_underside_pivot_fasteners':sum(o.name.startswith('HINGE_UNDER_SCREW_') for o in s.objects)==4,'eight_small_keeper_pads':sum(o.name.startswith('HINGE_UNDER_KEEPER_') for o in s.objects)==8,'four_arm_inserts_follow_the_arm_pivots':all(bpy.data.objects['ARM_UNDER_INSERT_'+tag].parent==bpy.data.objects['ARM_'+tag+'_ROOT'] for tag in ['FL','FR','RL','RR']),'20_connector_contacts':sum(o.name.startswith('BELLY_PORT_CONTACT_') for o in s.objects)==20,'all_material_slots_assigned':all(m is not None for name in primary for m in bpy.data.objects[name].data.materials)}
report={'checks':checks,'preserved_objects':len(before),'unexpected_changes':unexpected,'max_preserved_world_error_m':max_error,'upper_cradle_surface_error_m':upper_error,'topology':topologies,'fitted_face_clearance':fit,'aperture_tests':openings};(ROOT/'renders/exterior-v14/validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));assert all(checks.values())
