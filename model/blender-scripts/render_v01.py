"""Render matching V01 views and archive exact copies under teach/shots."""
import bpy
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
scene = bpy.context.scene
if Path(bpy.data.filepath).resolve() != (root/"blender/drone-v01.blend"):
    raise RuntimeError("Open blender/drone-v01.blend before running this script.")
for frame, pose in [(1,"unfolded"),(121,"folded")]:
    scene.frame_set(frame)
    for angle in ("front","side","top","back","three-quarter"):
        name = f"v01-{pose}-{angle}.png"
        dest = root/"renders/v01"/name
        scene.camera = bpy.data.objects["Studio.camera."+angle]
        scene.render.filepath = str(dest)
        # An interrupted batch can be resumed without changing completed shots.
        if not dest.exists():
            bpy.ops.render.render(write_still=True)
        shutil.copy2(dest, root/"teach/shots/v01"/name)
