import bpy
from pathlib import Path
R=Path(__file__).resolve().parents[2];bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v24.blend'));s=bpy.context.scene
s.cycles.samples=32;s.render.resolution_x=1200;s.render.resolution_y=900;s.render.resolution_percentage=100;bpy.data.objects['STUDIO_GROUND'].hide_render=True
for tag in ['FR','RL']:
 s.camera=bpy.data.objects['CAM_support_'+tag];s.render.filepath=str(R/'renders/exterior-v24'/('support-'+tag+'-native.png'));bpy.ops.render.render(write_still=True)
print('V24_NATIVE_RENDERS_COMPLETE',flush=True)
