"""Render the saved editable V12 model for close inspection."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v12.blend'))
s=bpy.context.scene;s.cycles.samples=48;s.render.resolution_x=1536;s.render.resolution_y=1024;s.render.resolution_percentage=100
for name in ['hero','front_arm_detail','front_hinge','rear_arm_detail','rear_hinge']:
 s.camera=bpy.data.objects['CAM_'+name];s.render.filepath=str(ROOT/'renders/exterior-v12'/(name+'.png'));bpy.ops.render.render(write_still=True)
print('V12_RENDERS_COMPLETE')
