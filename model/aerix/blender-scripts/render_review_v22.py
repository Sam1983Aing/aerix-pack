import bpy
from pathlib import Path
R=Path(__file__).resolve().parents[2];bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v22.blend'));s=bpy.context.scene
s.cycles.samples=40;s.render.resolution_x=1500;s.render.resolution_y=1050;s.render.resolution_percentage=100;bpy.data.objects['STUDIO_GROUND'].hide_render=True
for name in ['front_finish','front_left_finish','front_right_finish']:
 s.camera=bpy.data.objects['CAM_'+name];s.render.filepath=str(R/'renders/exterior-v22'/(name+'-native.png'));bpy.ops.render.render(write_still=True)
print('V22_FINAL_RENDERS_COMPLETE',flush=True)
