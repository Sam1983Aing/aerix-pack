"""Export the two existing V15 cutaway scenes for a local browser review."""
from pathlib import Path
import bpy

project = Path(__file__).resolve().parents[1]
assert Path(bpy.data.filepath).resolve() == project / 'blender/drone-v15.blend'
for view in ('Top', 'Side'):
    scene = bpy.data.scenes[f'Review 6 · {view} section']
    bpy.context.window.scene = scene
    bpy.ops.object.select_all(action='DESELECT')
    for obj in scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=str(project / 'viewer/interior' / f'{view.lower()}.glb'),
        export_format='GLB', use_active_scene=True, use_selection=True,
        export_animations=False, export_texcoords=False, export_cameras=False,
        export_lights=False, export_yup=True,
    )

