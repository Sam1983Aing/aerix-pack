"""Render the final native joint and shell-edge inspection cameras."""
import bpy
from pathlib import Path
R=Path(__file__).resolve().parents[2];bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v20.blend'));s=bpy.context.scene
s.cycles.samples=40;s.render.resolution_percentage=100;s.render.resolution_x=1400;s.render.resolution_y=900
bpy.data.objects['STUDIO_GROUND'].hide_render=True;bpy.data.objects['LIGHT_REAR_INSPECTION_UNDER'].hide_render=False
for name in ['seam_left','seam_right','joint_left','joint_right','joint_low']:
 s.camera=bpy.data.objects['CAM_'+name];s.render.filepath=str(R/'renders/exterior-v20'/(name+'-native.png'));bpy.ops.render.render(write_still=True)
print('V20_NATIVE_RENDERS_COMPLETE',flush=True)
