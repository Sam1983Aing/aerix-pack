"""Inspect the continuous underside and retained rear charging/data connector."""
import bpy
from pathlib import Path
R=Path(__file__).resolve().parents[2];bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v19.blend'));s=bpy.context.scene;s.cycles.samples=48;s.render.resolution_percentage=100
for name in ['rear_underside','underside_body','rear_body']:
 bpy.data.objects['STUDIO_GROUND'].hide_render=True;bpy.data.objects['LIGHT_REAR_INSPECTION_UNDER'].hide_render=False
 s.render.resolution_x=1300 if name=='underside_body' else 1440;s.render.resolution_y=1500 if name=='underside_body' else 1100;s.camera=bpy.data.objects['CAM_'+name]
 if name=='underside_body':s.camera.data.ortho_scale=.32
 s.render.filepath=str(R/'renders/exterior-v19'/(name+'.png'));bpy.ops.render.render(write_still=True)
print('V19_RENDERS_COMPLETE',flush=True)
