"""Render the actual section meshes and the five locked exterior studio views."""
from pathlib import Path
import bpy,sys
root=Path(__file__).resolve().parents[1]
assert Path(bpy.data.filepath).resolve()==root/'blender/drone-v15.blend'
dest=root/'renders/v15';dest.mkdir(exist_ok=True)
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='METAL';prefs.refresh_devices()
    for device in prefs.devices:device.use=device.type=='METAL'
    gpu=any(d.use for d in prefs.devices)
except Exception:gpu=False
def write(s,name):
    final=dest/(name+'.png');tmp=dest/('.pending-'+name+'.png')
    bpy.context.window.scene=s
    s.cycles.device='GPU' if gpu else 'CPU'
    s.render.filepath=str(tmp)
    bpy.ops.render.render(write_still=True,scene=s.name)
    tmp.replace(final);print('RENDERED',name,flush=True)
if '--studio-only' not in sys.argv:
    for n in ['Top','Side']:
        s=bpy.data.scenes['Review 6 · '+n+' section'];write(s,'section-'+n.lower())
if '--sections-only' not in sys.argv:
    s=bpy.data.scenes['V15 · Assembled'];s.frame_set(1)
    for n in ['three-quarter','top','side','front','back']:
        s.camera=bpy.data.objects['Studio.camera.'+n];s.cycles.samples=48 if n=='three-quarter' else 28
        write(s,'studio-'+n)

