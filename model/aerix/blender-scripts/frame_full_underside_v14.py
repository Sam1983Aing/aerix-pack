import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v14.blend'))
s=bpy.context.scene;bpy.data.objects['CAM_underside_full'].data.ortho_scale=.76
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v14.blend'))
s.camera=bpy.data.objects['CAM_underside_full'];s.cycles.samples=40;s.render.resolution_x=1536;s.render.resolution_y=1024;s.render.resolution_percentage=100
bpy.data.objects['STUDIO_GROUND'].hide_render=True;bpy.data.objects['LIGHT_REAR_INSPECTION_UNDER'].hide_render=False
s.render.filepath=str(ROOT/'renders/exterior-v14/underside_full.png');bpy.ops.render.render(write_still=True)
