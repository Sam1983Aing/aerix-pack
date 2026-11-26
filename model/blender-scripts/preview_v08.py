from pathlib import Path
import bpy
root=Path(__file__).resolve().parents[1]
sc=bpy.context.scene
sc.render.resolution_percentage=55
sc.cycles.samples=5
for f,view in [(1,'top'),(1,'three-quarter'),(121,'three-quarter')]:
    sc.frame_set(f)
    sc.camera=bpy.data.objects['Studio.camera.'+view]
    sc.render.filepath=str(root/f'measurements/v08-draft-{f}-{view}.png')
    bpy.ops.render.render(write_still=True)
