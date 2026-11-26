"""Render the three V14a edge macros and all locked V14 studio cameras."""
from pathlib import Path
import runpy
import sys
import bpy
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from v14a_views import render_details
scene=bpy.context.scene
assert Path(bpy.data.filepath).resolve()==root/'blender/drone-v14a.blend'
if '--metal' in sys.argv:
    preferences=bpy.context.preferences.addons['cycles'].preferences
    preferences.compute_device_type='METAL'
    preferences.refresh_devices()
    for device in preferences.devices:
        device.use=device.type=='METAL'
    if any(d.use for d in preferences.devices):
        scene.cycles.device='GPU'
render_details(root/'renders/v14a','v14a')
scene.cycles.samples=48
bpy.data.objects['Studio.floor'].hide_render=False
scene.camera=bpy.data.objects['Studio.camera.three-quarter']
runpy.run_path(str(root/'scripts/render_revision.py'),run_name='__main__')
