import bpy,json
from pathlib import Path
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v06.blend'))
s=bpy.context.scene;cam=bpy.data.objects['CAM_hero'];deps=bpy.context.evaluated_depsgraph_get()
points=[]
for ob in s.objects:
 if ob.type not in ['MESH','CURVE','FONT'] or ob.hide_render or ob.name=='STUDIO_GROUND':continue
 ev=ob.evaluated_get(deps)
 mesh=ev.to_mesh()
 for v in mesh.vertices:points.append(world_to_camera_view(s,cam,ev.matrix_world@v.co))
 ev.to_mesh_clear()
checks={'eight_blades':sum(o.name.startswith('BLADE_') for o in s.objects)==8,'two_recessed_glass_elements':sum(o.name.startswith('STEREO_GLASS_') for o in s.objects)==2,'two_visible_pupils':sum(o.name.startswith('STEREO_CENTER_') for o in s.objects)==2,'hero_not_cropped':all(0<p.x<1 and 0<p.y<1 and p.z>0 for p in points),'no_live_boolean_cutters':not any(m.type=='BOOLEAN' for o in s.objects for m in o.modifiers)}
report={'checks':checks,'hero_projected_bounds':[min(p.x for p in points),max(p.x for p in points),min(p.y for p in points),max(p.y for p in points)]}
(ROOT/'renders/exterior-v06/validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));assert all(checks.values())
