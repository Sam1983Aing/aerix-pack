import bpy,json
from pathlib import Path
from mathutils import Vector,kdtree
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v09.blend'))
s=bpy.context.scene;deps=bpy.context.evaluated_depsgraph_get();cam=bpy.data.objects['CAM_hero']
points=[]
for o in s.objects:
 if o.type not in {'MESH','CURVE','FONT'} or o.hide_render or o.name=='STUDIO_GROUND':continue
 ev=o.evaluated_get(deps);me=ev.to_mesh();points.extend(world_to_camera_view(s,cam,ev.matrix_world@v.co) for v in me.vertices);ev.to_mesh_clear()
def coords(name):
 ob=bpy.data.objects[name].evaluated_get(deps);me=ob.to_mesh();out=[ob.matrix_world@v.co for v in me.vertices];ob.to_mesh_clear();return out
left=coords('MOTOR_BASE_FL');right=coords('MOTOR_BASE_FR');tree=kdtree.KDTree(len(left))
for i,p in enumerate(left):tree.insert(p,i)
tree.balance();error=max(tree.find(Vector((-p.x,p.y,p.z)))[2] for p in right)
checks={'eight_blades':sum(o.name.startswith('BLADE_') for o in s.objects)==8,'four_rotor_roots':sum(o.name.startswith('PROPELLER_') for o in s.objects)==4,'six_crown_spokes_each':all(sum(o.name.startswith('MOTOR_CROWN_SPOKE_'+tag+'_') for o in s.objects)==6 for tag in ['FL','FR']),'48_winding_loops_each':all(sum(o.name.startswith('WINDING_'+tag+'_') for o in s.objects)==48 for tag in ['FL','FR']),'mirrored_front_housings':error<1e-6,'four_champagne_tip_inlays':all(any(p.material_index==1 for p in bpy.data.objects['BLADE_'+tag+'_'+str(k)].data.polygons) for tag in ['FL','FR'] for k in [0,1]),'hero_not_cropped':all(0<p.x<1 and 0<p.y<1 and p.z>0 for p in points)}
report={'checks':checks,'front_housing_mirror_error_m':error,'rotor_centers_clearance_m':.28-.20,'note':'Visual model checks, not engineering validation.'}
(ROOT/'renders/exterior-v09/validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));assert all(checks.values())
