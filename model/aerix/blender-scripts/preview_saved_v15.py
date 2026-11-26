import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v15.blend'))
s=bpy.context.scene;s.cycles.samples=20;s.render.resolution_percentage=70
for name in ['body_contours','top_body']:
 s.camera=bpy.data.objects['CAM_'+name];s.render.resolution_x=1000 if name=='top_body' else 1536;s.render.resolution_y=1400 if name=='top_body' else 1024;bpy.data.objects['STUDIO_GROUND'].hide_render=name=='top_body';s.render.filepath=str(ROOT/'renders/exterior-v15'/(name+'-preview.png'));bpy.ops.render.render(write_still=True)
