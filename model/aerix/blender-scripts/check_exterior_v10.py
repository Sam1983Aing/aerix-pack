"""Geometry and assembly checks for the rear-arm refinement."""
import bpy,json,hashlib,array,re
from pathlib import Path
from mathutils import Vector,kdtree
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[2]
def below(ob,names):
 while ob:
  if ob.name in names:return True
  ob=ob.parent
 return False
def preserved_geometry():
 deps=bpy.context.evaluated_depsgraph_get();result={}
 for ob in bpy.context.scene.objects:
  if ob.type not in {'MESH','CURVE','FONT'} or ob.hide_render or ob.name=='STUDIO_GROUND' or below(ob,{'ARM_RL_ROOT','ARM_RR_ROOT'}):continue
  ev=ob.evaluated_get(deps);me=ev.to_mesh();vs=array.array('f',[0])*(len(me.vertices)*3);me.vertices.foreach_get('co',vs)
  indices=array.array('i',[0])*len(me.loops);me.loops.foreach_get('vertex_index',indices)
  h=hashlib.sha256(vs.tobytes()+indices.tobytes()+str(tuple(tuple(row) for row in ev.matrix_world)).encode()+str([m.name if m else None for m in me.materials]).encode()).hexdigest();result[ob.name]=h;ev.to_mesh_clear()
 return result
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v09.blend'));before=preserved_geometry()
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v10.blend'));after=preserved_geometry()
s=bpy.context.scene;deps=bpy.context.evaluated_depsgraph_get()
def coords(ob):
 ev=ob.evaluated_get(deps);me=ev.to_mesh();out=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear();return out
left=coords(bpy.data.objects['MOTOR_BASE_RL']);right=coords(bpy.data.objects['MOTOR_BASE_RR']);tree=kdtree.KDTree(len(left))
for i,p in enumerate(left):tree.insert(p,i)
tree.balance();error=max(tree.find(Vector((-p.x,p.y,p.z)))[2] for p in right)
def framed(camera,tag=None):
 cam=bpy.data.objects['CAM_'+camera];points=[]
 for ob in s.objects:
  if ob.type not in {'MESH','CURVE','FONT'} or ob.hide_render or ob.name=='STUDIO_GROUND':continue
  if tag and not below(ob,{'PROPELLER_'+tag}) and ob.name not in {'MOTOR_BASE_'+tag,'FOOT_PAD_'+tag}:continue
  points.extend(world_to_camera_view(s,cam,p) for p in coords(ob))
 return all(0<p.x<1 and 0<p.y<1 and p.z>0 for p in points)
tags=['FL','FR','RL','RR']
checks={'body_front_arms_and_optics_unchanged':before==after,'eight_blades':sum(o.name.startswith('BLADE_') for o in s.objects)==8,'four_rotor_roots':sum(o.name.startswith('PROPELLER_') for o in s.objects)==4,'six_crown_spokes_each_motor':all(sum(o.name.startswith('MOTOR_CROWN_SPOKE_'+tag+'_') for o in s.objects)==6 for tag in tags),'48_winding_loops_each_motor':all(sum(o.name.startswith('WINDING_'+tag+'_') for o in s.objects)==48 for tag in tags),'mirrored_rear_housings':error<1e-6,'eight_champagne_tip_inlays':all(any(p.material_index==1 for p in bpy.data.objects['BLADE_'+tag+'_'+str(k)].data.polygons) for tag in tags for k in [0,1]),'two_rear_leg_inserts':all('REAR_LEG_INSERT_'+tag in bpy.data.objects for tag in ['RL','RR']),'hero_not_cropped':framed('hero'),'rear_right_blades_and_leg_not_cropped':framed('rear_right','RR'),'rear_left_blades_and_leg_not_cropped':framed('rear_left','RL')}
report={'checks':checks,'preserved_objects':len(before),'changed_outside_rear_arms':[k for k in before.keys()|after.keys() if before.get(k)!=after.get(k)],'rear_housing_mirror_error_m':error,'conservative_rotor_disk_clearance_m':.28-.20}
(ROOT/'renders/exterior-v10/validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));assert all(checks.values())
