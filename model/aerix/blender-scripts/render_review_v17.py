"""Render the main camera, lens macro, gimbal, front integration and full drone."""
import bpy
from pathlib import Path
R=Path(__file__).resolve().parents[2];bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v17.blend'));s=bpy.context.scene;s.render.resolution_percentage=100;s.cycles.samples=64
for name in ['main_camera','main_lens','gimbal_side','front_camera','hero']:
 s.render.resolution_x=1400 if name=='main_lens' else 1536;s.render.resolution_y=1400 if name=='main_lens' else 1024;s.camera=bpy.data.objects['CAM_'+name];s.render.filepath=str(R/'renders/exterior-v17'/(name+'.png'));bpy.ops.render.render(write_still=True)
print('V17_RENDERS_COMPLETE')
