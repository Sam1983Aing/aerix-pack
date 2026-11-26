"""Final studio and underside views from the saved V14 model."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v14.blend'))
s=bpy.context.scene;s.cycles.samples=40;s.render.resolution_percentage=100
for name in ['hero','underside_full','underside_body','underside_oblique','underside_sensors','underside_rear_joint','underside_front_joint']:
 s.render.resolution_x=1200 if name=='underside_body' else 1536;s.render.resolution_y=1500 if name=='underside_body' else 1024
 s.camera=bpy.data.objects['CAM_'+name];under=name!='hero';bpy.data.objects['STUDIO_GROUND'].hide_render=under;bpy.data.objects['LIGHT_REAR_INSPECTION_UNDER'].hide_render=not under
 s.render.filepath=str(ROOT/'renders/exterior-v14'/(name+'.png'));bpy.ops.render.render(write_still=True)
print('V14_RENDERS_COMPLETE')
