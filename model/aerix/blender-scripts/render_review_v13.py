"""Studio and structural inspection renders from the saved V13 model."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v13.blend'))
s=bpy.context.scene;s.cycles.samples=40;s.render.resolution_x=1536;s.render.resolution_y=1024;s.render.resolution_percentage=100
for name in ['hero','rear_connection','rear_connections_under','rear_connections_top','rear_connection_low']:
 s.camera=bpy.data.objects['CAM_'+name];under=name in ['rear_connections_under','rear_connection_low'];bpy.data.objects['STUDIO_GROUND'].hide_render=under;bpy.data.objects['LIGHT_REAR_INSPECTION_UNDER'].hide_render=not under
 s.render.filepath=str(ROOT/'renders/exterior-v13'/(name+'.png'));bpy.ops.render.render(write_still=True)
print('V13_RENDERS_COMPLETE')
