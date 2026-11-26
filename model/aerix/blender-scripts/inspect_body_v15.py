import bpy,json
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v14.blend'))
s=bpy.context.scene;deps=bpy.context.evaluated_depsgraph_get()
for ob in s.objects:
 if ob.name.startswith(('BODY_','FRONT_VISOR','VISOR_','STEREO_','SHELL_SEAM','REAR_FASCIA','STATUS_LIGHT','AERIX_WORD')):
  ev=ob.evaluated_get(deps);p=[ob.matrix_world@Vector(v) for v in ev.bound_box]
  print('PART',ob.name,ob.type,'bounds',[(min(v[i] for v in p),max(v[i] for v in p)) for i in range(3)],'mods',[m.type for m in ob.modifiers])
s.cycles.samples=16;s.render.resolution_x=900;s.render.resolution_y=1300;s.render.resolution_percentage=70
cam=s.camera=bpy.data.objects['CAM_top'];cam.location=(0,0,.7);cam.rotation_euler=(0,0,0);cam.data.type='ORTHO';cam.data.ortho_scale=.38
bpy.data.objects['STUDIO_GROUND'].hide_render=True;s.render.filepath=str(ROOT/'renders/exterior-v15/v14-top-before.png');bpy.ops.render.render(write_still=True)
