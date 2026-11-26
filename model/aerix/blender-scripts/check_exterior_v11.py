"""Rear-panel openings, local scope preservation, symmetry and review framing."""
import bpy,json,hashlib,array
from pathlib import Path
from mathutils import Vector,kdtree
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[2]
def changed_part(name):return name in {'BODY_SHELL_TOP','BODY_CRADLE'} or name.startswith('SHELL_SEAM_') or (name.startswith('REAR_') and not name.startswith('REAR_LEG_'))
def snapshot():
 deps=bpy.context.evaluated_depsgraph_get();signatures={};front={}
 for ob in bpy.context.scene.objects:
  if ob.type not in {'MESH','CURVE','FONT'} or ob.hide_render or ob.name=='STUDIO_GROUND':continue
  ev=ob.evaluated_get(deps);me=ev.to_mesh()
  if ob.name in {'BODY_SHELL_TOP','BODY_CRADLE'}:front[ob.name]=[ev.matrix_world@v.co for v in me.vertices if v.co.y<.035]
  if not changed_part(ob.name):
   vs=array.array('f',[0])*(len(me.vertices)*3);me.vertices.foreach_get('co',vs);indices=array.array('i',[0])*len(me.loops);me.loops.foreach_get('vertex_index',indices)
   signatures[ob.name]=hashlib.sha256(vs.tobytes()+indices.tobytes()+str(tuple(tuple(row) for row in ev.matrix_world)).encode()+str([m.name if m else None for m in me.materials]).encode()).hexdigest()
  ev.to_mesh_clear()
 return signatures,front
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v10.blend'));before,front_before=snapshot()
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v11.blend'));after,front_after=snapshot()
s=bpy.context.scene;deps=bpy.context.evaluated_depsgraph_get()
def distance(left,right,mirror=False):
 tree=kdtree.KDTree(len(left))
 for i,p in enumerate(left):tree.insert(p,i)
 tree.balance();return max(tree.find(Vector((-p.x,p.y,p.z)) if mirror else p)[2] for p in right)
front_errors={name:distance(front_before[name],front_after[name]) for name in front_before}
def coords(ob):
 ev=ob.evaluated_get(deps);me=ev.to_mesh();vs=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear();return vs
shell=coords(bpy.data.objects['BODY_SHELL_TOP']);mirror=distance(shell,shell,True)
def framed(camera,only_rear=False):
 cam=bpy.data.objects['CAM_'+camera];pts=[]
 for ob in s.objects:
  if ob.type not in {'MESH','CURVE','FONT'} or ob.hide_render or ob.name=='STUDIO_GROUND':continue
  if only_rear and (not ob.name.startswith('REAR_') or ob.name.startswith('REAR_LEG_')):continue
  pts.extend(world_to_camera_view(s,cam,p) for p in coords(ob))
 return all(0<p.x<1 and 0<p.y<1 and p.z>0 for p in pts)
fascia=bpy.data.objects['REAR_FASCIA'].evaluated_get(deps)
openings=[(0,.0790),(0,.0595)]+[(sign*.025,z) for sign in [-1,1] for z in [.0815,.0764]]
misses=[not fascia.ray_cast(Vector((x,.20,z)),Vector((0,-1,0)))[0] for x,z in openings]
hit,p,n,idx=fascia.ray_cast(Vector((0,.20,.089)),Vector((0,-1,0)))
checks={'arms_optics_and_other_details_unchanged':before==after,'front_shell_and_cradle_preserved':all(e<1e-6 for e in front_errors.values()),'symmetric_shell_within_10_microns':mirror<1e-5,'four_vents_port_and_cover_are_true_openings':all(misses),'rear_fascia_outward_normals':hit and n.y>.9,'24_recessed_connector_contacts':sum(o.name.startswith('REAR_PORT_CONTACT_') for o in s.objects)==24,'eight_blades':sum(o.name.startswith('BLADE_') for o in s.objects)==8,'four_rotor_roots':sum(o.name.startswith('PROPELLER_') for o in s.objects)==4,'hero_not_cropped':framed('hero'),'rear_overview_not_cropped':framed('rear_three_quarter'),'rear_panel_detail_framed':framed('rear_body',True)}
report={'checks':checks,'preserved_objects':len(before),'unexpected_changes':[k for k in before.keys()|after.keys() if before.get(k)!=after.get(k)],'front_surface_max_error_m':front_errors,'shell_mirror_error_m':mirror}
(ROOT/'renders/exterior-v11/validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));assert all(checks.values())
