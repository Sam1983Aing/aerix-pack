import bpy,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v23.blend'));s=bpy.context.scene
s.cycles.samples=40;s.render.resolution_x=1500;s.render.resolution_y=1050;s.render.resolution_percentage=100;bpy.data.objects['STUDIO_GROUND'].hide_render=True
for name in (['rear_vent_finish'] if '--macro-only' in sys.argv else ['rear_finish','rear_left_finish','rear_right_finish','rear_vent_finish']):
 s.camera=bpy.data.objects['CAM_'+name];s.render.filepath=str(R/'renders/exterior-v23'/(name+'-native.png'));bpy.ops.render.render(write_still=True)
print('V23_FINAL_RENDERS_COMPLETE',flush=True)
