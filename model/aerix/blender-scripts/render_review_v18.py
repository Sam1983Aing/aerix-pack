"""Final underside inspection views with consistent studio lighting."""
import bpy,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v18.blend'));s=bpy.context.scene;s.cycles.samples=56;s.render.resolution_percentage=100
preview='--preview' in sys.argv
if preview:s.cycles.samples=24;s.render.resolution_percentage=70
for name in (['underside_sensors'] if preview else ['underside_body','underside_sensors','underside_oblique','hero']):
 under=name!='hero';bpy.data.objects['STUDIO_GROUND'].hide_render=under;bpy.data.objects['LIGHT_REAR_INSPECTION_UNDER'].hide_render=not under
 s.render.resolution_x=1300 if name=='underside_body' else 1536;s.render.resolution_y=1500 if name=='underside_body' else 1024
 s.camera=bpy.data.objects['CAM_'+name]
 if name=='underside_body':s.camera.data.ortho_scale=.32
 if name=='underside_sensors':s.camera.data.ortho_scale=.115
 s.render.filepath=str(R/'renders/exterior-v18'/(name+('-preview' if preview else '')+'.png'));bpy.ops.render.render(write_still=True)
print('V18_RENDERS_COMPLETE',flush=True)
