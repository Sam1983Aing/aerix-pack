import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-interior-v04.blend'))
s=bpy.context.scene
bpy.data.objects['CAM_EXPLODED'].data.ortho_scale=.83
s.frame_set(1);s.camera=bpy.data.objects['CAM_hero']
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/aerix-interior-v04.blend'))
s.frame_set(90);s.camera=bpy.data.objects['CAM_EXPLODED'];s.render.filepath=str(ROOT/'renders/interior-v04/exploded.png')
bpy.ops.render.render(write_still=True)
